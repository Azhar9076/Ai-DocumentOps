"""Regex/heuristic structured field extraction with per-field confidence scoring."""

from __future__ import annotations

import re

from app.models import DocType
from app.pipeline.schemas_extraction import (
    SCHEMA_BY_TYPE,
    ContractSchema,
    FieldCandidate,
    FormSchema,
    InvoiceSchema,
)

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
}

PATTERNS_BY_TYPE = {
    DocType.INVOICE: INVOICE_PATTERNS,
    DocType.FORM: FORM_PATTERNS,
    DocType.CONTRACT: CONTRACT_PATTERNS,
}

NUMERIC_KEYS = {"subtotal", "tax_amount", "total_amount", "contract_value", "term_months"}
AMBIGUITY_MARKERS = ("?", "|", "~", "illegible", "unclear")


def parse_money(raw: str) -> float | None:
    cleaned = re.sub(r"[^\d\.\-]", "", raw)
    if not cleaned or cleaned in {"-", ".", "-."}:
        return None
    try:
        return round(float(cleaned), 2)
    except ValueError:
        return None


LABEL_BOUNDARY = re.compile(r"\s{2,}|\s(?=[A-Z][A-Za-z ]{2,24}\s*:)")


def _clean_value(raw: str) -> str:
    """Trim a captured value at the next label boundary (OCR lines often run on)."""
    value = LABEL_BOUNDARY.split(raw.strip(), maxsplit=1)[0]
    return value.strip().rstrip(".,;:")


def _score(raw_value: str, key: str, ocr_quality: float, pattern_rank: int) -> float:
    """Confidence combines OCR quality, pattern specificity, and value cleanliness."""
    score = 0.62 + 0.33 * ocr_quality
    score -= 0.06 * pattern_rank
    value = raw_value.strip()
    if not value:
        return 0.0
    if key in NUMERIC_KEYS:
        score += 0.06 if parse_money(value) is not None else -0.35
    if any(marker in value.lower() for marker in AMBIGUITY_MARKERS):
        score -= 0.22
    if len(value) <= 2:
        score -= 0.12
    if len(value) > 90:
        score -= 0.08
    if re.search(r"[^\w\s@\.\,\-\/\$\&\(\)%#:']", value):
        score -= 0.1
    return round(max(0.05, min(0.99, score)), 4)


def extract_fields(
    text: str, doc_type: DocType, ocr_quality: float
) -> tuple[list[FieldCandidate], dict[str, object]]:
    """Extract schema fields; returns candidates and the validated schema payload."""
    patterns = PATTERNS_BY_TYPE.get(doc_type)
    if patterns is None:
        return [], {}

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    candidates: list[FieldCandidate] = []
    payload: dict[str, object] = {}

    for key, key_patterns in patterns.items():
        best: FieldCandidate | None = None
        for rank, pattern in enumerate(key_patterns):
            regex = re.compile(pattern, re.IGNORECASE)
            for line_no, line in enumerate(lines):
                match = regex.search(line)
                if not match:
                    continue
                raw = _clean_value(match.group(1))
                confidence = _score(raw, key, ocr_quality, rank)
                if best is None or confidence > best.confidence_score:
                    best = FieldCandidate(
                        field_key=key,
                        field_value=raw,
                        confidence_score=confidence,
                        bbox=f"line:{line_no}",
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


def _coerce(key: str, value: str) -> object:
    if key in NUMERIC_KEYS:
        parsed = parse_money(value)
        if key == "term_months" and parsed is not None:
            return int(parsed)
        return parsed
    return value


__all__ = [
    "ContractSchema",
    "FormSchema",
    "InvoiceSchema",
    "extract_fields",
    "parse_money",
]
