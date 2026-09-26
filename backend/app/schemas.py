from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models import DocStatus, DocType


class FieldOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    field_key: str
    field_value: str
    confidence_score: float
    is_validated: bool
    bbox: str | None = None


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    action: str
    performed_by: str
    timestamp: datetime
    details: str
    run_number: int = 1
    elapsed_ms: int = 0


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    field_key: str
    original_value: str
    corrected_value: str
    reviewer_id: str
    reviewed_at: datetime


class ValidationIssue(BaseModel):
    rule: str
    message: str
    severity: str = "error"
    fields: list[str] = Field(default_factory=list)


class DocumentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    doc_type: DocType
    status: DocStatus
    overall_confidence: float
    uploaded_at: datetime
    processing_ms: int
    audit_summary: str = ""


class DocumentDetail(DocumentSummary):
    file_path: str
    mime_type: str
    page_count: int
    raw_text: str
    fields: list[FieldOut] = Field(default_factory=list)
    reviews: list[ReviewOut] = Field(default_factory=list)
    audit_logs: list[AuditLogOut] = Field(default_factory=list)
    validation_issues: list[ValidationIssue] = Field(default_factory=list)


class FieldEdit(BaseModel):
    field_key: str
    field_value: str


class ReviewSubmission(BaseModel):
    edits: list[FieldEdit] = Field(default_factory=list)
    reviewer_id: str = "reviewer@documentops.ai"
    decision: str = "APPROVE"  # APPROVE | REJECT
    note: str = ""


class BulkReviewSubmission(BaseModel):
    document_ids: list[str] = Field(default_factory=list)
    decision: str = "APPROVE"
    reviewer_id: str = "reviewer@documentops.ai"


class RoutingThresholds(BaseModel):
    auto_approved_min: float
    needs_review_min: float


class FieldCorrection(BaseModel):
    field_name: str
    corrected_value: str
    reviewer_id: str = "reviewer@documentops.ai"


class MetricsOut(BaseModel):
    documents_processed: int
    auto_automation_rate: float
    reviews_pending: int
    average_confidence: float
    estimated_hours_saved: float
    math_errors_intercepted: int = 0
    status_breakdown: dict[str, int]
    confidence_distribution: list[dict[str, float | str | int]]
    accuracy_trend: list[dict[str, float | str]]
    roi_metrics: dict[str, Any] = Field(default_factory=dict)


class QualityOut(BaseModel):
    overall_accuracy: float
    routing_accuracy: float = 0.0
    field_accuracy: list[dict[str, float | str | int]]
    math_validation_pass_rate: float
    human_correction_rate: float
    confidence_calibration: list[dict[str, Any]] = Field(default_factory=list)
    accuracy_iterations: list[dict[str, Any]] = Field(default_factory=list)
    roi_metrics: dict[str, Any] = Field(default_factory=dict)
    sample_size: int
    notice: str
    v1_comparison: dict[str, Any] | None = None


class BenchmarkRunOut(BaseModel):
    iteration: int
    field_accuracy: float
    routing_accuracy: float
    avg_latency_ms: float
    total_samples: int
    timestamp: str
    calibration: list[dict[str, Any]]
