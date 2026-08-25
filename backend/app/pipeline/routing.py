"""Confidence-based routing decisions."""

from __future__ import annotations

from app.config import settings
from app.models import DocStatus
from app.pipeline.schemas_extraction import FieldCandidate


def overall_confidence(candidates: list[FieldCandidate], classification_confidence: float) -> float:
    if not candidates:
        return round(min(classification_confidence, 0.4), 4)
    field_avg = sum(c.confidence_score for c in candidates) / len(candidates)
    weakest = min(c.confidence_score for c in candidates)
    blended = 0.6 * field_avg + 0.25 * weakest + 0.15 * classification_confidence
    return round(max(0.0, min(1.0, blended)), 4)


def route(confidence: float, has_rule_failure: bool) -> DocStatus:
    if has_rule_failure or confidence < settings.review_threshold:
        return DocStatus.ACTION_REQUIRED
    if confidence >= settings.auto_approve_threshold:
        return DocStatus.AUTO_APPROVED
    return DocStatus.NEEDS_REVIEW
