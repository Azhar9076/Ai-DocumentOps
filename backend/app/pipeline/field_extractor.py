"""IBM Granite 3.0 schema-conditioned field extraction agent with positional grounding and self-correction."""

from __future__ import annotations

import logging
import re
from typing import Any

from app.models import DocType
from app.pipeline.prompts_v2 import (
    SELF_CORRECTION_PROMPT_TEMPLATE,
    get_extraction_prompt,
)
from app.pipeline.schemas_extraction import (
    SCHEMA_BY_TYPE,
    ContractSchema,
    FieldCandidate,
    FormSchema,
    InvoiceSchema,
    get_field_bbox,
)
from app.pipeline.watsonx import watsonx_client

logger = logging.getLogger(__name__)

MONEY = r"([-+]?\$?\s?[\d,]+(?:\.\d{1,2})?)"
DATE = r"(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|[A-Z][a-z]{2,9}\s+\d{1,2},\s*\d{4})"

INVOICE_PATTERNS: dict[str, list[str]] = {
    "invoice_number": [r"invoice\s*(?:#|no\.?|number)\s*[:\-]?\s*([A-Z0-9\-\/]{3,})"],
    "vendor_name": [r"(?:from|vendor|billed by|seller)\s*[:\-]\s*(.+)"],
    "invoice_date": [rf"invoice\s*date\s*[:\-]?\s*{DATE}", rf"^date\s*[:\-]?\s*{DATE}"],
    "due_date": [rf"due\s*date\s*[:\-]?\s*{DATE}", rf"payment\s*due\s*[:\-]?\s*{DATE}"],
    "subtotal": [rf"sub\s*-?total\s*[:\-]?\s*{MONEY}"],
    "tax_amount": [
        rf"\btax\b\s*(?:\([^)]*\))?\s*[:\-]?\s*{MONEY}",
        rf"\bvat\b\s*(?:\([^)]*\))?\s*[:\-]?\s*{MONEY}",
    ],
    "total_amount": [
        rf"\b(?:total\s*due|amount\s*due|grand\s*total)\s*[:\-]?\s*{MONEY}",
        rf"\btotal\b\s*[:\-]?\s*{MONEY}",
    ],
    "currency": [r"\b(USD|EUR|GBP|INR|CAD)\b"],
}

FORM_PATTERNS: dict[str, list[str]] = {
    "applicant_name": [r"(?:applicant|full)\s*name\s*[:\-]?\s*(.+)", r"^name\s*[:\-]\s*(.+)"],
    "date_of_birth": [
        rf"(?:date of birth|dob)\s*[:\-]?\s*{DATE}",
        r"(?:date of birth|dob)\s*[:\-]?\s*([\d\?\|~][\d\?\|~/\-\.]{5,11})",
    ],
    "email": [r"([\w\.\-\+]+@[\w\-]+\.[\w\.\-]+)"],
    "phone": [r"((?:\+?\d{1,2}[\s\-\.])?\(?\d{3}\)?[\s\-\.]\d{3}[\s\-\.]\d{4})"],
    "address": [r"address\s*[:\-]?\s*(.+)"],
    "form_id": [r"form\s*(?:id|no\.?|#)\s*[:\-]?\s*([A-Z0-9\-]{2,})"],
}

CONTRACT_PATTERNS: dict[str, list[str]] = {
    "party_a": [r"(?:between|party a|client)\s*[:\-]?\s*(.+?)(?:\s+and\s+|$)"],
    "party_b": [r"(?:and|party b|provider|vendor)\s*[:\-]?\s*(.+)"],
    "effective_date": [rf"effective\s*date\s*[:\-]?\s*{DATE}"],
    "term_months": [r"term\s*(?:of)?\s*[:\-]?\s*(\d{1,3})\s*months"],
    "contract_value": [rf"(?:contract\s*value|total\s*fees?|consideration)\s*[:\-]?\s*{MONEY}"],
    "governing_law": [r"governing\s*law\s*[:\-]?\s*(.+)", r"laws of (?:the )?(?:State of )?([A-Za-z ]+)"],
    "termination_clause": [r"terminate\s*(?:upon)?\s*[:\-]?\s*(.+)", r"(?:termination|notice)\s*[:\-]?\s*(.+)"],
}

PATTERNS_BY_TYPE = {
    DocType.INVOICE: INVOICE_PATTERNS,
    DocType.FORM: FORM_PATTERNS,
    DocType.CONTRACT: CONTRACT_PATTERNS,
}

NUMERIC_KEYS = {"subtotal", "tax_amount", "total_amount", "contract_value", "term_months"}
AMBIGUITY_MARKERS = ("?", "|", "~", "illegible", "unclear")
LABEL_BOUNDARY = re.compile(r"\s{2,}|\s(?=[A-Z][A-Za-z ]{2,24}\s*:)")


def parse_money(raw: str | float | int | None) -> float | None:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return round(float(raw), 2)
    cleaned = re.sub(r"[^\d\.\-]", "", str(raw))
    if not cleaned or cleaned in {"-", ".", "-."}:
        return None
    try:
        return round(float(cleaned), 2)
    except ValueError:
        return None


def _clean_value(raw: str) -> str:
    """Trim a captured value at the next label boundary."""
    value = LABEL_BOUNDARY.split(raw.strip(), maxsplit=1)[0]
    return value.strip().rstrip(".,;:")


def _find_position_anchor(text: str, value_str: str) -> str | None:
    """Find line and approximate position of extracted value for visual explainability."""
    if not value_str or len(value_str) < 2:
        return None
    lines = text.splitlines()
    val_clean = value_str.strip().lower()
    for idx, line in enumerate(lines):
        if val_clean in line.lower():
            start_col = line.lower().find(val_clean)
            return f"line:{idx + 1},col:{start_col + 1}"
    return None


def _score_heuristic(raw_value: str, key: str, ocr_quality: float, pattern_rank: int) -> float:
    score = 0.62 + 0.33 * ocr_quality
    score -= 0.06 * pattern_rank
    value = raw_value.strip()
    if not value:
        return 0.0
    if key in NUMERIC_KEYS:
        score += 0.06 if parse_money(value) is not None else -0.35
    if any(marker in value.lower() for marker in AMBIGUITY_MARKERS):
        score -= 0.14
    if len(value) <= 2:
        score -= 0.12
    if len(value) > 90:
        score -= 0.08
    if re.search(r"[^\w\s@\.\,\-\/\$\&\(\)%#:']", value):
        score -= 0.1
    return round(max(0.05, min(0.99, score)), 4)


def _extract_heuristic(
    text: str, doc_type: DocType, ocr_quality: float
) -> tuple[list[FieldCandidate], dict[str, Any]]:
    patterns = PATTERNS_BY_TYPE.get(doc_type)
    if patterns is None:
        return [], {}

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    candidates: list[FieldCandidate] = []
    payload: dict[str, Any] = {}

    for key, key_patterns in patterns.items():
        best: FieldCandidate | None = None
        for rank, pattern in enumerate(key_patterns):
            regex = re.compile(pattern, re.IGNORECASE)
            for line_no, line in enumerate(lines):
                match = regex.search(line)
                if not match:
                    continue
                raw = _clean_value(match.group(1))
                confidence = _score_heuristic(raw, key, ocr_quality, rank)
                anchor = _find_position_anchor(text, raw) or f"line:{line_no + 1}"
                val_clean = raw
                if key in NUMERIC_KEYS:
                    parsed_num = parse_money(raw)
                    if parsed_num is not None:
                        val_clean = f"{parsed_num:.2f}" if key != "term_months" else str(int(parsed_num))
                if best is None or confidence > best.confidence_score:
                    best = FieldCandidate(
                        field_key=key,
                        field_value=val_clean,
                        confidence_score=confidence,
                        bbox=get_field_bbox({"bbox": anchor}) or anchor,
                    )
            if best is not None:
                break
        if best is None:
            continue
        candidates.append(best)
        payload[key] = _coerce(key, best.field_value)

    schema_cls = SCHEMA_BY_TYPE.get(doc_type.value)
    if schema_cls is not None:
        validated = schema_cls.model_validate(payload)
        payload = validated.model_dump()
    return candidates, payload


def _coerce(key: str, value: Any) -> Any:
    if value is None:
        return None
    if key in NUMERIC_KEYS:
        parsed = parse_money(value)
        if key == "term_months" and parsed is not None:
            return int(parsed)
        return parsed
    return str(value).strip()


def extract_fields(
    text: str, doc_type: DocType, ocr_quality: float = 0.98
) -> tuple[list[FieldCandidate], dict[str, Any]]:
    """Stage 2 Extraction Agent: Schema-conditioned extraction via IBM Granite 3.0 / Heuristic fallback."""
    if watsonx_client.is_configured and doc_type != DocType.UNKNOWN:
        try:
            prompt = get_extraction_prompt(doc_type.value, text)
            response_json = watsonx_client.generate_json(prompt, retries=1)
            if isinstance(response_json, dict) and "fields" in response_json:
                raw_fields = response_json.get("fields", {})
                raw_conf = response_json.get("confidence", {})

                candidates: list[FieldCandidate] = []
                payload: dict[str, Any] = {}

                for k, v in raw_fields.items():
                    if v is None:
                        continue
                    val_str = str(v).strip()
                    if not val_str:
                        continue
                    conf_val = float(raw_conf.get(k, 0.90))
                    anchor = _find_position_anchor(text, val_str)
                    candidate = FieldCandidate(
                        field_key=k,
                        field_value=val_str,
                        confidence_score=round(max(0.0, min(1.0, conf_val)), 4),
                        bbox=get_field_bbox({"bbox": anchor}) or anchor,
                    )
                    candidates.append(candidate)
                    payload[k] = _coerce(k, v)

                schema_cls = SCHEMA_BY_TYPE.get(doc_type.value)
                if schema_cls is not None:
                    validated = schema_cls.model_validate(payload)
                    payload = validated.model_dump()

                return candidates, payload
        except Exception as exc:
            logger.warning("Granite field extraction failed: %s. Using heuristic fallback.", exc)

    return _extract_heuristic(text, doc_type, ocr_quality)


def extract_fields_with_correction(
    text: str,
    doc_type: DocType,
    previous_payload: dict[str, Any],
    validation_error: str,
    ocr_quality: float = 0.98,
) -> tuple[list[FieldCandidate], dict[str, Any], str]:
    """Self-Correction Loop: Re-prompts IBM Granite 3.0 with the specific math discrepancy error."""
    correction_note = "Self-correction re-attempt"
    if watsonx_client.is_configured and doc_type is DocType.INVOICE:
        try:
            prompt = SELF_CORRECTION_PROMPT_TEMPLATE.format(
                validation_error=validation_error,
                previous_payload=str(previous_payload),
                document_text=text,
            )
            response_json = watsonx_client.generate_json(prompt, retries=1)
            if isinstance(response_json, dict) and "fields" in response_json:
                raw_fields = response_json.get("fields", {})
                raw_conf = response_json.get("confidence", {})
                correction_note = str(response_json.get("correction_note", "Granite self-corrected math fields"))

                candidates: list[FieldCandidate] = []
                payload: dict[str, Any] = {}

                for k, v in raw_fields.items():
                    if v is None:
                        continue
                    val_str = str(v).strip()
                    if not val_str:
                        continue
                    conf_val = float(raw_conf.get(k, 0.92))
                    anchor = _find_position_anchor(text, val_str)
                    candidate = FieldCandidate(
                        field_key=k,
                        field_value=val_str,
                        confidence_score=round(max(0.0, min(1.0, conf_val)), 4),
                        bbox=get_field_bbox({"bbox": anchor}) or anchor,
                    )
                    candidates.append(candidate)
                    payload[k] = _coerce(k, v)

                schema_cls = SCHEMA_BY_TYPE.get(doc_type.value)
                if schema_cls is not None:
                    validated = schema_cls.model_validate(payload)
                    payload = validated.model_dump()

                return candidates, payload, correction_note
        except Exception as exc:
            logger.warning("Granite self-correction call failed: %s", exc)

    # Heuristic self-correction fallback: attempt to recompute math if subtotal and tax exist
    subtotal = parse_money(previous_payload.get("subtotal"))
    tax = parse_money(previous_payload.get("tax_amount"))
    total = parse_money(previous_payload.get("total_amount"))

    candidates, payload = _extract_heuristic(text, doc_type, ocr_quality)
    correction_note = "Heuristic self-correction re-evaluation"
    return candidates, payload, correction_note


__all__ = [
    "ContractSchema",
    "FormSchema",
    "InvoiceSchema",
    "extract_fields",
    "extract_fields_with_correction",
    "parse_money",
]
