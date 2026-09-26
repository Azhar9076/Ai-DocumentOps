"""IBM Granite 3.0 + heuristic fallback document classification agent."""

from __future__ import annotations

import logging
import re
from typing import Any

from app.models import DocType
from app.pipeline.prompts_v2 import CLASSIFIER_PROMPT_TEMPLATE
from app.pipeline.watsonx import watsonx_client

logger = logging.getLogger(__name__)

KEYWORDS: dict[DocType, dict[str, float]] = {
    DocType.INVOICE: {
        "invoice": 3.0,
        "invoice number": 3.0,
        "bill to": 2.0,
        "subtotal": 2.5,
        "tax": 1.5,
        "total due": 2.5,
        "amount due": 2.5,
        "purchase order": 1.5,
        "remit to": 2.0,
    },
    DocType.FORM: {
        "application": 2.5,
        "form": 2.0,
        "applicant": 3.0,
        "date of birth": 3.0,
        "signature": 1.0,
        "please print": 2.0,
        "checkbox": 1.5,
        "patient intake": 3.0,
    },
    DocType.CONTRACT: {
        "agreement": 3.0,
        "party": 2.0,
        "hereby": 2.0,
        "term of this": 2.0,
        "governing law": 3.0,
        "effective date": 2.0,
        "witness whereof": 3.0,
        "non-disclosure": 3.0,
        "services agreement": 3.0,
    },
}


def classify_heuristic(text: str) -> tuple[DocType, float, str]:
    """Fast keyword-scored heuristic classifier fallback."""
    haystack = text.lower()
    scores: dict[DocType, float] = {}
    for doc_type, keywords in KEYWORDS.items():
        score = 0.0
        for keyword, weight in keywords.items():
            hits = len(re.findall(re.escape(keyword), haystack))
            if hits:
                score += weight * min(hits, 3)
        scores[doc_type] = score

    best_type, best_score = max(scores.items(), key=lambda kv: kv[1])
    if best_score == 0:
        return DocType.UNKNOWN, 0.3, "No recognizable classification keywords found"

    total = sum(scores.values()) or 1.0
    margin = best_score / total
    confidence = min(0.99, 0.55 + margin * 0.45)
    return best_type, round(confidence, 4), f"Heuristic match for {best_type.value}"


def classify(text: str) -> tuple[DocType, float]:
    """Synchronous interface returning (DocType, confidence)."""
    doc_type, conf, _ = classify_with_metadata(text)
    return doc_type, conf


def classify_with_metadata(text: str) -> tuple[DocType, float, dict[str, Any]]:
    """Execute Stage 1: Granite 3.0 Document Classifier Agent with heuristic fallback."""
    if watsonx_client.is_configured:
        try:
            prompt = CLASSIFIER_PROMPT_TEMPLATE.format(document_text=text[:4000])
            result = watsonx_client.generate_json(prompt, retries=1)
            if isinstance(result, dict):
                raw_type = str(result.get("doc_type", "")).upper()
                conf = float(result.get("confidence", 0.85))
                reasoning = str(result.get("reasoning", "Classified by IBM Granite 3.0"))
                
                type_map = {
                    "INVOICE": DocType.INVOICE,
                    "CONTRACT": DocType.CONTRACT,
                    "FORM": DocType.FORM,
                    "UNKNOWN": DocType.UNKNOWN,
                }
                detected_type = type_map.get(raw_type, DocType.UNKNOWN)
                return detected_type, round(conf, 4), {
                    "source": "IBM Granite 3.0",
                    "reasoning": reasoning,
                    "raw_response": result,
                }
        except Exception as exc:
            logger.warning("Granite classifier invocation failed: %s. Using heuristic fallback.", exc)

    doc_type, conf, reason = classify_heuristic(text)
    return doc_type, conf, {"source": "Heuristic Rules", "reasoning": reason}
