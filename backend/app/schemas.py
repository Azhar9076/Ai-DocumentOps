from __future__ import annotations

from datetime import datetime

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


class MetricsOut(BaseModel):
    documents_processed: int
    auto_automation_rate: float
    reviews_pending: int
    average_confidence: float
    estimated_hours_saved: float
    status_breakdown: dict[str, int]
    confidence_distribution: list[dict[str, float | str | int]]
    accuracy_trend: list[dict[str, float | str]]


class QualityOut(BaseModel):
    overall_accuracy: float
    field_accuracy: list[dict[str, float | str | int]]
    math_validation_pass_rate: float
    human_correction_rate: float
    sample_size: int
    notice: str
