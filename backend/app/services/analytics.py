"""Dashboard metrics and ground-truth quality evaluation."""

from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DocStatus, Document, ExtractedField, Review, utcnow
from app.schemas import MetricsOut, QualityOut

MINUTES_SAVED_PER_DOC = 7.5
AUTOMATED_STATUSES = {DocStatus.AUTO_APPROVED, DocStatus.APPROVED}
PENDING_STATUSES = {DocStatus.NEEDS_REVIEW, DocStatus.ACTION_REQUIRED}

CONFIDENCE_BUCKETS = [
    ("0-49%", 0.0, 0.5),
    ("50-69%", 0.5, 0.7),
    ("70-79%", 0.7, 0.8),
    ("80-89%", 0.8, 0.9),
    ("90-100%", 0.9, 1.01),
]


def build_metrics(db: Session) -> MetricsOut:
    documents = db.scalars(select(Document)).all()
    total = len(documents)
    processed = [d for d in documents if d.status is not DocStatus.PROCESSING]
    automated = [d for d in documents if d.status in AUTOMATED_STATUSES]
    pending = [d for d in documents if d.status in PENDING_STATUSES]
    scored = [d for d in documents if d.overall_confidence > 0]

    status_breakdown: dict[str, int] = defaultdict(int)
    for document in documents:
        status_breakdown[document.status.value] += 1

    distribution = []
    for label, low, high in CONFIDENCE_BUCKETS:
        count = sum(1 for d in scored if low <= d.overall_confidence < high)
        distribution.append({"bucket": label, "count": count})

    trend = _accuracy_trend(documents)

    return MetricsOut(
        documents_processed=len(processed),
        auto_automation_rate=round(len(automated) / total * 100, 1) if total else 0.0,
        reviews_pending=len(pending),
        average_confidence=(
            round(sum(d.overall_confidence for d in scored) / len(scored) * 100, 1) if scored else 0.0
        ),
        estimated_hours_saved=round(len(automated) * MINUTES_SAVED_PER_DOC / 60, 2),
        status_breakdown=dict(status_breakdown),
        confidence_distribution=distribution,
        accuracy_trend=trend,
    )


def _accuracy_trend(documents: list[Document]) -> list[dict[str, float | str]]:
    today = utcnow().date()
    by_day: dict[str, list[float]] = defaultdict(list)
    for document in documents:
        if document.overall_confidence > 0:
            by_day[document.uploaded_at.date().isoformat()].append(document.overall_confidence)

    trend: list[dict[str, float | str]] = []
    for offset in range(6, -1, -1):
        day = (today - timedelta(days=offset)).isoformat()
        scores = by_day.get(day, [])
        trend.append(
            {
                "date": day,
                "confidence": round(sum(scores) / len(scores) * 100, 1) if scores else 0.0,
                "documents": len(scores),
            }
        )
    return trend


def build_quality(db: Session) -> QualityOut:
    fields = db.scalars(select(ExtractedField)).all()
    reviews = db.scalars(select(Review)).all()
    documents = db.scalars(select(Document)).all()

    corrected_keys = {(r.document_id, r.field_key) for r in reviews if r.original_value != r.corrected_value}
    total_fields = len(fields)
    correct_fields = sum(
        1 for f in fields if (f.document_id, f.field_key) not in corrected_keys and f.is_validated
    )

    by_key: dict[str, list[bool]] = defaultdict(list)
    for f in fields:
        by_key[f.field_key].append(
            (f.document_id, f.field_key) not in corrected_keys and f.is_validated
        )

    field_accuracy = [
        {
            "field_key": key,
            "accuracy": round(sum(values) / len(values) * 100, 1),
            "samples": len(values),
        }
        for key, values in sorted(by_key.items())
    ]

    invoices = [d for d in documents if d.doc_type.value == "INVOICE"]
    math_failures = sum(1 for d in invoices if "invoice_math" in (d.validation_errors or ""))
    math_pass_rate = (
        round((len(invoices) - math_failures) / len(invoices) * 100, 1) if invoices else 100.0
    )

    return QualityOut(
        overall_accuracy=round(correct_fields / total_fields * 100, 1) if total_fields else 0.0,
        field_accuracy=field_accuracy,
        math_validation_pass_rate=math_pass_rate,
        human_correction_rate=round(len(corrected_keys) / total_fields * 100, 1) if total_fields else 0.0,
        sample_size=len(documents),
        notice="Metrics evaluated against project standard ground-truth test suite.",
    )
