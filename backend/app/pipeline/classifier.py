"""Keyword-scored document classification."""

from __future__ import annotations

import re

from app.models import DocType

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
    },
    DocType.FORM: {
        "application": 2.5,
        "form": 2.0,
        "applicant": 3.0,
        "date of birth": 3.0,
        "signature": 1.0,
        "please print": 2.0,
        "checkbox": 1.5,
    },
    DocType.CONTRACT: {
        "agreement": 3.0,
        "party": 2.0,
        "hereby": 2.0,
        "term of this": 2.0,
        "governing law": 3.0,
        "effective date": 2.0,
        "witness whereof": 3.0,
    },
}


def classify(text: str) -> tuple[DocType, float]:
    """Return the detected document type plus a 0-1 classification confidence."""
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
        return DocType.UNKNOWN, 0.3

    total = sum(scores.values()) or 1.0
    margin = best_score / total
    confidence = min(0.99, 0.55 + margin * 0.45)
    return best_type, round(confidence, 4)
