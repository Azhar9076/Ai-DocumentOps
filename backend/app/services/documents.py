"""Document persistence, storage and human-review services."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import BinaryIO

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import DocStatus, Document, ExtractedField, Review, new_id, utcnow
from app.pipeline.extraction import SUPPORTED_SUFFIXES
from app.pipeline.runner import log_audit
from app.schemas import DocumentDetail, ReviewSubmission, ValidationIssue

MAX_BYTES = 25 * 1024 * 1024
SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def store_upload(db: Session, filename: str, mime_type: str, stream: BinaryIO) -> Document:
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{suffix}'. Allowed: {sorted(SUPPORTED_SUFFIXES)}",
        )

    document_id = new_id()
    safe_name = SAFE_NAME.sub("_", Path(filename).name) or f"document{suffix}"
    target_dir = settings.storage_dir / document_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / safe_name

    with target.open("wb") as out:
        shutil.copyfileobj(stream, out, length=1024 * 1024)

    size = target.stat().st_size
    if size == 0 or size > MAX_BYTES:
        shutil.rmtree(target_dir, ignore_errors=True)
        raise HTTPException(status_code=413, detail="File is empty or exceeds the 25MB limit.")

    document = Document(
        id=document_id,
        filename=safe_name,
        file_path=str(target),
        mime_type=mime_type or "application/octet-stream",
        status=DocStatus.UPLOADED,
    )
    db.add(document)
    db.flush()
    log_audit(db, document.id, "UPLOADED", json.dumps({"filename": safe_name, "bytes": size}))
    db.commit()
    return document


def get_document(db: Session, document_id: str) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


def list_documents(db: Session, status: str | None = None, limit: int = 100) -> list[Document]:
    stmt = select(Document).order_by(Document.uploaded_at.desc()).limit(limit)
    if status:
        stmt = stmt.where(Document.status == DocStatus(status))
    return list(db.scalars(stmt))


def to_detail(document: Document) -> DocumentDetail:
    issues = [ValidationIssue(**item) for item in json.loads(document.validation_errors or "[]")]
    detail = DocumentDetail.model_validate(document, from_attributes=True)
    detail.validation_issues = issues
    return detail


def submit_review(db: Session, document: Document, submission: ReviewSubmission) -> Document:
    if submission.decision not in {"APPROVE", "REJECT"}:
        raise HTTPException(status_code=400, detail="decision must be APPROVE or REJECT")

    fields = {f.field_key: f for f in document.fields}
    for edit in submission.edits:
        field: ExtractedField | None = fields.get(edit.field_key)
        if field is None:
            raise HTTPException(status_code=400, detail=f"Unknown field '{edit.field_key}'")
        if field.field_value == edit.field_value:
            continue
        db.add(
            Review(
                document_id=document.id,
                field_key=edit.field_key,
                original_value=field.field_value,
                corrected_value=edit.field_value,
                reviewer_id=submission.reviewer_id,
            )
        )
        log_audit(
            db,
            document.id,
            "FIELD_CORRECTED",
            json.dumps(
                {
                    "field_key": edit.field_key,
                    "from": field.field_value,
                    "to": edit.field_value,
                    "prior_confidence": field.confidence_score,
                }
            ),
            performed_by=submission.reviewer_id,
        )
        field.field_value = edit.field_value
        field.confidence_score = 1.0
        field.is_validated = True

    if submission.decision == "REJECT":
        document.status = DocStatus.REJECTED
    else:
        document.status = DocStatus.APPROVED
        document.validation_errors = "[]"
        for field in document.fields:
            field.is_validated = True

    if document.fields:
        document.overall_confidence = round(
            sum(f.confidence_score for f in document.fields) / len(document.fields), 4
        )

    log_audit(
        db,
        document.id,
        f"HUMAN_{submission.decision}",
        json.dumps(
            {
                "edits": len(submission.edits),
                "note": submission.note,
                "reviewed_at": utcnow().isoformat(),
            }
        ),
        performed_by=submission.reviewer_id,
    )
    db.commit()
    db.refresh(document)
    return document
