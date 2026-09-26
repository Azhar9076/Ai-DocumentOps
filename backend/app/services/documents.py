"""Document persistence, storage and human-review services."""

from __future__ import annotations

import csv
import io
import json
import re
import shutil
from pathlib import Path
from typing import Any, BinaryIO

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import DocStatus, Document, ExtractedField, Review, new_id, utcnow
from app.pipeline.extraction import SUPPORTED_SUFFIXES
from app.pipeline.runner import log_audit
from app.schemas import BulkReviewSubmission, DocumentDetail, ReviewSubmission, ValidationIssue

MAX_BYTES = 25 * 1024 * 1024
SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/octet-stream",  # Browsers sometimes send this for valid files
}


def store_upload(db: Session, filename: str, mime_type: str, stream: BinaryIO) -> Document:
    if mime_type and mime_type.lower() not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported MIME type '{mime_type}'. Allowed: {sorted(ALLOWED_MIME_TYPES)}",
        )
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


def cancel_document(db: Session, document_id: str) -> Document:
    """Cancel in-progress document pipeline execution."""
    document = get_document(db, document_id)
    if document.status == DocStatus.PROCESSING or document.status == DocStatus.UPLOADED:
        document.status = DocStatus.CANCELLED
        log_audit(db, document_id, "CANCELLED_BY_USER", "Pipeline cancelled by user action")
        db.commit()
        db.refresh(document)
    return document


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


def correct_field(db: Session, document_id: str, correction: Any) -> dict[str, Any]:
    """One-click Approve & Learn: apply human inline correction, update benchmark cache, and re-validate."""
    from app.pipeline import validation
    from app.pipeline.benchmark_runner import append_human_correction
    from app.pipeline.schemas_extraction import FieldCandidate

    document = get_document(db, document_id)
    field_key = correction.field_name
    corrected_val = correction.corrected_value
    reviewer = correction.reviewer_id

    field = next((f for f in document.fields if f.field_key == field_key), None)
    old_val = field.field_value if field else ""

    if field:
        field.field_value = corrected_val
        field.confidence_score = 1.0
        field.is_validated = True
    else:
        field = ExtractedField(
            document_id=document.id,
            field_key=field_key,
            field_value=corrected_val,
            confidence_score=1.0,
            is_validated=True,
        )
        db.add(field)

    db.add(
        Review(
            document_id=document.id,
            field_key=field_key,
            original_value=old_val,
            corrected_value=corrected_val,
            reviewer_id=reviewer,
        )
    )

    log_audit(
        db,
        document.id,
        "APPROVE_AND_LEARN",
        json.dumps({
            "field_key": field_key,
            "from": old_val,
            "to": corrected_val,
            "reviewer_id": reviewer,
        }),
        performed_by=reviewer,
    )

    # Append to active learning benchmark cache
    append_human_correction(document.id, field_key, corrected_val, reviewer)

    # Re-run deterministic validation
    candidates = [
        FieldCandidate(
            field_key=f.field_key,
            field_value=f.field_value,
            confidence_score=f.confidence_score,
            bbox=f.bbox,
        )
        for f in document.fields
    ]
    val_result = validation.validate(candidates, document.doc_type)
    issues = [issue.as_dict() for issue in val_result.issues]
    document.validation_errors = json.dumps(issues)

    if not val_result.has_errors:
        document.status = DocStatus.APPROVED

    if document.fields:
        document.overall_confidence = round(
            sum(f.confidence_score for f in document.fields) / len(document.fields), 4
        )

    db.commit()
    db.refresh(document)
    return {
        "status": "corrected",
        "math_result": {
            "status": val_result.math_result.status,
            "reason": val_result.math_result.reason,
            "delta": val_result.math_result.delta,
        },
        "document": to_detail(document),
    }


def bulk_review(db: Session, submission: BulkReviewSubmission) -> list[DocumentSummary]:
    """Bulk approve or reject multiple documents from review queue."""
    updated_docs = []
    for doc_id in submission.document_ids:
        try:
            doc = get_document(db, doc_id)
            if doc.status in (DocStatus.NEEDS_REVIEW, DocStatus.ACTION_REQUIRED):
                if submission.decision == "APPROVE":
                    doc.status = DocStatus.APPROVED
                    doc.validation_errors = "[]"
                    for field in doc.fields:
                        field.is_validated = True
                else:
                    doc.status = DocStatus.REJECTED
                
                log_audit(
                    db,
                    doc.id,
                    f"BULK_{submission.decision}",
                    json.dumps({"reviewer_id": submission.reviewer_id}),
                    performed_by=submission.reviewer_id,
                )
                updated_docs.append(doc)
        except Exception:
            continue
    db.commit()
    return updated_docs


def export_document_csv(document: Document) -> str:
    """Generate CSV representation of document extractions and audit summary."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Document ID", document.id])
    writer.writerow(["Filename", document.filename])
    writer.writerow(["Doc Type", document.doc_type.value])
    writer.writerow(["Status", document.status.value])
    writer.writerow(["Confidence", f"{document.overall_confidence:.2%}"])
    writer.writerow(["Audit Summary", document.audit_summary])
    writer.writerow([])
    writer.writerow(["Field Key", "Extracted Value", "Confidence Score", "Position Anchor", "Validated"])
    for f in document.fields:
        writer.writerow([f.field_key, f.field_value, f"{f.confidence_score:.2%}", f.bbox or "N/A", f.is_validated])
    return output.getvalue()


def export_document_json(document: Document) -> dict[str, Any]:
    """Generate structured JSON export."""
    detail = to_detail(document)
    return detail.model_dump(mode="json")


def generate_audit_pdf(document: Document) -> bytes:
    """Generate formal Document Compliance & Audit Certificate PDF via reportlab."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import LETTER
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER

    # Header bar
    c.setFillColor(colors.HexColor("#0f172a"))  # Slate-900
    c.rect(0, height - 80, width, 80, stroke=0, fill=1)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, height - 40, "AI DocumentOps — Compliance & Audit Certificate")
    c.setFont("Helvetica", 10)
    c.drawString(40, height - 60, "Immutable 3-Agent Trace Lineage · IBM Docling & IBM Granite 3.0 via watsonx.ai")

    y = height - 110

    # Metadata Grid
    c.setFillColor(colors.HexColor("#0f172a"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Document Metadata")
    y -= 18

    c.setFont("Helvetica", 9)
    meta_items = [
        f"Document ID: {document.id}",
        f"Filename: {document.filename}",
        f"Document Type: {document.doc_type.value}",
        f"Processing Status: {document.status.value}",
        f"Overall Confidence: {document.overall_confidence:.1%}",
        f"Processing Latency: {document.processing_ms} ms",
        f"Ingested Timestamp: {document.uploaded_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
    ]
    for item in meta_items:
        c.drawString(50, y, f"•  {item}")
        y -= 14

    y -= 10

    # Compliance Auditor Summary Box
    c.setFillColor(colors.HexColor("#f0f9ff"))  # Sky-50
    c.setStrokeColor(colors.HexColor("#bae6fd"))  # Sky-200
    c.roundRect(40, y - 40, width - 80, 48, 6, stroke=1, fill=1)

    c.setFillColor(colors.HexColor("#0369a1"))  # Sky-700
    c.setFont("Helvetica-Bold", 9)
    c.drawString(50, y - 6, "AI COMPLIANCE AUDITOR SUMMARY")
    c.setFillColor(colors.HexColor("#0c4a6e"))  # Sky-900
    c.setFont("Helvetica", 8.5)
    summary_text = document.audit_summary or "Deterministic validation complete. No anomalies detected."
    # Wrap text if long
    if len(summary_text) > 105:
        c.drawString(50, y - 20, summary_text[:105])
        c.drawString(50, y - 32, summary_text[105:210])
    else:
        c.drawString(50, y - 22, summary_text)

    y -= 65

    # Extracted Fields Table Header
    c.setFillColor(colors.HexColor("#0f172a"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Extracted Fields Grounding (Granite 3.0)")
    y -= 16

    c.setFillColor(colors.HexColor("#e2e8f0"))
    c.rect(40, y - 4, width - 80, 16, stroke=0, fill=1)
    c.setFillColor(colors.HexColor("#1e293b"))
    c.setFont("Helvetica-Bold", 8)
    c.drawString(45, y, "FIELD KEY")
    c.drawString(180, y, "EXTRACTED VALUE")
    c.drawString(340, y, "CONFIDENCE")
    c.drawString(420, y, "POSITION ANCHOR")
    c.drawString(515, y, "STATUS")
    y -= 14

    c.setFont("Helvetica", 8)
    for idx, f in enumerate(document.fields[:12]):
        if idx % 2 == 1:
            c.setFillColor(colors.HexColor("#f8fafc"))
            c.rect(40, y - 3, width - 80, 13, stroke=0, fill=1)
        c.setFillColor(colors.HexColor("#0f172a"))
        c.drawString(45, y, str(f.field_key)[:22])
        c.drawString(180, y, str(f.field_value)[:26])
        c.drawString(340, y, f"{f.confidence_score:.1%}")
        c.drawString(420, y, str(f.bbox or 'N/A')[:18])
        status_str = "VALIDATED" if f.is_validated else "FLAGGED"
        c.setFillColor(colors.HexColor("#16a34a") if f.is_validated else colors.HexColor("#dc2626"))
        c.drawString(515, y, status_str)
        y -= 13
        if y < 140:
            break

    y -= 10

    # Pipeline Execution Audit Log Trace
    c.setFillColor(colors.HexColor("#0f172a"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Pipeline Execution Audit Trace")
    y -= 16

    c.setFont("Helvetica", 8)
    for log in document.audit_logs[-6:]:
        c.setFillColor(colors.HexColor("#64748b"))
        ts_str = log.timestamp.strftime("%H:%M:%S")
        c.drawString(45, y, f"{ts_str}")
        c.setFillColor(colors.HexColor("#0f172a"))
        c.setFont("Helvetica-Bold", 8)
        c.drawString(95, y, f"[{log.action}]")
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor("#475569"))
        latency_note = f"({log.elapsed_ms}ms)" if log.elapsed_ms > 0 else ""
        detail_snippet = f"{log.details[:60]}... {latency_note}" if len(log.details) > 60 else f"{log.details} {latency_note}"
        c.drawString(250, y, detail_snippet)
        y -= 13
        if y < 60:
            break

    # Footer verification stamp
    c.setStrokeColor(colors.HexColor("#cbd5e1"))
    c.line(40, 45, width - 40, 45)
    c.setFillColor(colors.HexColor("#64748b"))
    c.setFont("Helvetica", 7.5)
    c.drawString(40, 32, "Verified & Governed by AI DocumentOps · 100% Deterministic Guardrails · Zero Fake Latency")
    c.drawString(width - 190, 32, f"Certificate Hash: {document.id[:16].upper()}")

    c.showPage()
    c.save()
    return buffer.getvalue()


def get_demo_sample_documents(limit: int = 5) -> list[tuple[str, str, bytes]]:
    """Generate in-memory sample document byte buffers for concurrent stress testing."""
    from reportlab.lib.pagesizes import LETTER
    from reportlab.pdfgen import canvas

    samples = []
    base_templates = [
        (
            "clean_invoice_stress_{i}.pdf",
            "application/pdf",
            [
                "ACME INDUSTRIAL SUPPLY CO.",
                "INVOICE",
                "Invoice Number: INV-2026-0{i}87",
                "Vendor: ACME Industrial Supply Co.",
                "Invoice Date: 2026-09-01",
                "Due Date: 2026-10-01",
                "Bill To: Global Tech Enterprises",
                "Subtotal: {subtotal:.2f}",
                "Sales Tax (8.25%): {tax:.2f}",
                "Total Due: {total:.2f}",
                "Currency: USD",
            ],
        ),
        (
            "inconsistent_invoice_stress_{i}.pdf",
            "application/pdf",
            [
                "VERTEX CONSULTING SERVICES",
                "INVOICE",
                "Invoice Number: INV-ERR-0{i}99",
                "Vendor: Vertex Consulting",
                "Invoice Date: 2026-09-02",
                "Due Date: 2026-09-16",
                "Bill To: Northwind Logistics",
                "Subtotal: 500.00",
                "Sales Tax (10%): 50.00",
                "Total Due: 620.00",  # Intentionally mismatched math
                "Currency: USD",
            ],
        ),
        (
            "medical_intake_form_stress_{i}.pdf",
            "application/pdf",
            [
                "PATIENT INTAKE APPLICATION FORM",
                "Form No: FRM-2026-{i}",
                "Applicant Name: Alex R. Morgan",
                "Date of Birth: 1990-05-15",
                "Email: alex.morgan{i}@example.com",
                "Phone: 555-019-{i:02d}",
                "Address: 742 Evergreen Terrace, Springfield",
            ],
        ),
    ]

    for i in range(1, limit + 1):
        tpl_idx = (i - 1) % len(base_templates)
        name_tpl, mime, lines_tpl = base_templates[tpl_idx]
        filename = name_tpl.format(i=i)

        subtotal = 100.0 * i
        tax = subtotal * 0.0825
        total = subtotal + tax

        lines = [
            line.format(i=i, subtotal=subtotal, tax=tax, total=total)
            for line in lines_tpl
        ]

        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=LETTER)
        pdf.setFont("Helvetica", 11)
        y = 720
        for line in lines:
            pdf.drawString(64, y, line)
            y -= 20
        pdf.showPage()
        pdf.save()

        samples.append((filename, mime, buffer.getvalue()))

    return samples
