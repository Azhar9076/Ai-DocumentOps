from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return uuid.uuid4().hex


class Base(DeclarativeBase):
    pass


class DocType(str, enum.Enum):
    INVOICE = "INVOICE"
    FORM = "FORM"
    CONTRACT = "CONTRACT"
    UNKNOWN = "UNKNOWN"


class DocStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    AUTO_APPROVED = "AUTO_APPROVED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    filename: Mapped[str] = mapped_column(String(512))
    doc_type: Mapped[DocType] = mapped_column(Enum(DocType), default=DocType.UNKNOWN)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    status: Mapped[DocStatus] = mapped_column(Enum(DocStatus), default=DocStatus.UPLOADED)
    overall_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    file_path: Mapped[str] = mapped_column(String(1024), default="")
    mime_type: Mapped[str] = mapped_column(String(128), default="")
    page_count: Mapped[int] = mapped_column(Integer, default=1)
    raw_text: Mapped[str] = mapped_column(Text, default="")
    validation_errors: Mapped[str] = mapped_column(Text, default="[]")
    processing_ms: Mapped[int] = mapped_column(Integer, default=0)
    ibm_stack_version: Mapped[str] = mapped_column(String(128), default="")  # Track IBM stack versions used

    fields: Mapped[list[ExtractedField]] = relationship(
        back_populates="document", cascade="all, delete-orphan", order_by="ExtractedField.field_key"
    )
    reviews: Mapped[list[Review]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list[AuditLog]] = relationship(
        back_populates="document", cascade="all, delete-orphan", order_by="AuditLog.timestamp"
    )


class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    field_key: Mapped[str] = mapped_column(String(128))
    field_value: Mapped[str] = mapped_column(Text, default="")
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_validated: Mapped[bool] = mapped_column(Boolean, default=False)
    bbox: Mapped[str | None] = mapped_column(String(128), nullable=True)
    extraction_method: Mapped[str] = mapped_column(String(64), default="hybrid")  # ibm-granite, hybrid, regex
    context_snippet: Mapped[str] = mapped_column(Text, default="")  # Lineage context from Docling

    document: Mapped[Document] = relationship(back_populates="fields")


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    field_key: Mapped[str] = mapped_column(String(128))
    original_value: Mapped[str] = mapped_column(Text, default="")
    corrected_value: Mapped[str] = mapped_column(Text, default="")
    reviewer_id: Mapped[str] = mapped_column(String(128), default="reviewer@documentops.ai")
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    document: Mapped[Document] = relationship(back_populates="reviews")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    action: Mapped[str] = mapped_column(String(128))
    performed_by: Mapped[str] = mapped_column(String(128), default="system")
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    details: Mapped[str] = mapped_column(Text, default="")

    document: Mapped[Document] = relationship(back_populates="audit_logs")
