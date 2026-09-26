"""Three Sequential Agents (Classifier -> Extractor -> Validator + Auditor) with Self-Correction Loop."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.db import get_db_session
from app.models import AuditLog, DocStatus, DocType, Document, ExtractedField
from app.pipeline import (
    auditor,
    classifier,
    extraction,
    field_extractor,
    routing,
    validation,
)
from app.pipeline.validation import MathCheckDecision, decide_math_validation

logger = logging.getLogger(__name__)

PIPELINE_STEPS = [
    "Uploaded",
    "Layout Parsing (Docling)",
    "Classifier Agent (Granite 3.0)",
    "Field Extractor Agent (Granite 3.0)",
    "Deterministic Validation Engine",
    "AI Compliance Auditor",
    "Complete",
]


@dataclass
class PipelineOutcome:
    status: DocStatus
    confidence: float
    issues: list[dict[str, Any]]
    audit_summary: str = ""
    self_corrected: bool = False


def get_latest_run_number(db: Session, document_id: str) -> int:
    from sqlalchemy import func, select
    max_run = db.scalar(
        select(func.max(AuditLog.run_number)).where(AuditLog.document_id == document_id)
    )
    return int(max_run) if max_run is not None else 0


def log_audit(
    db: Session,
    document_id: str,
    action: str,
    details: str,
    performed_by: str = "system",
    run_number: int = 1,
    elapsed_ms: int = 0,
) -> None:
    db.add(
        AuditLog(
            document_id=document_id,
            action=action,
            details=details,
            performed_by=performed_by,
            run_number=run_number,
            elapsed_ms=elapsed_ms,
        )
    )


def process_document_sync(db: Session, document: Document) -> PipelineOutcome:
    """Execute the full 3-agent pipeline with scoped database sessions, run versioning, and self-correction."""
    document_id = document.id
    started = time.perf_counter()

    # Determine run number
    with get_db_session() as session:
        prev_run = get_latest_run_number(session, document_id)
        run_number = prev_run + 1 if prev_run > 0 else 1

    # Initial setup
    document.status = DocStatus.PROCESSING
    log_audit(
        db,
        document_id,
        "PIPELINE_STARTED",
        json.dumps({"run_number": run_number, "note": "Three-Agent Pipeline execution started"}),
        run_number=run_number,
        elapsed_ms=0,
    )
    db.commit()

    try:
        # Stage 0: Layout Parsing & OCR (Docling)
        s0_start = time.perf_counter()
        file_path = Path(document.file_path)
        text, page_count, ocr_quality = extraction.extract_text(file_path)
        s0_ms = int((time.perf_counter() - s0_start) * 1000)
        
        with get_db_session() as session:
            doc = session.get(Document, document_id)
            if not doc or doc.status == DocStatus.CANCELLED:
                return PipelineOutcome(status=DocStatus.CANCELLED, confidence=0.0, issues=[])
            doc.raw_text = text[:200_000]
            doc.page_count = page_count
            log_audit(
                session,
                document_id,
                "DOCLING_PARSED",
                json.dumps({
                    "chars": len(text),
                    "pages": page_count,
                    "ocr_quality": ocr_quality,
                    "engine": "IBM Docling / OCR",
                }),
                run_number=run_number,
                elapsed_ms=s0_ms,
            )

        # Stage 1: Classifier Agent (Granite 3.0)
        s1_start = time.perf_counter()
        doc_type, class_conf, class_meta = classifier.classify_with_metadata(text)
        s1_ms = int((time.perf_counter() - s1_start) * 1000)
        with get_db_session() as session:
            doc = session.get(Document, document_id)
            if not doc or doc.status == DocStatus.CANCELLED:
                return PipelineOutcome(status=DocStatus.CANCELLED, confidence=0.0, issues=[])
            doc.doc_type = doc_type
            log_audit(
                session,
                document_id,
                "AGENT_CLASSIFIER",
                json.dumps({
                    "doc_type": doc_type.value,
                    "confidence": class_conf,
                    "meta": class_meta,
                }),
                run_number=run_number,
                elapsed_ms=s1_ms,
            )

        # Stage 2: Schema-Conditioned Extractor Agent (Granite 3.0)
        s2_start = time.perf_counter()
        candidates, payload = field_extractor.extract_fields(text, doc_type, ocr_quality)
        s2_ms = int((time.perf_counter() - s2_start) * 1000)
        with get_db_session() as session:
            doc = session.get(Document, document_id)
            if not doc or doc.status == DocStatus.CANCELLED:
                return PipelineOutcome(status=DocStatus.CANCELLED, confidence=0.0, issues=[])
            log_audit(
                session,
                document_id,
                "AGENT_EXTRACTOR_ATTEMPT_1",
                json.dumps({
                    "fields_count": len(candidates),
                    "payload": payload,
                    "prompt_version": "prompt_v2.1",
                }, default=str),
                run_number=run_number,
                elapsed_ms=s2_ms,
            )

        # Stage 3: Deterministic Rule & Arithmetic Validation
        s3_start = time.perf_counter()
        val_result = validation.validate(candidates, doc_type)
        self_corrected = False

        # Section 8: Self-Correction Feedback Loop
        # Triggers on: (a) math mismatch, or (b) required invoice math fields not extracted
        values_map = {c.field_key: c.field_value for c in candidates}
        math_decision = decide_math_validation(doc_type, values_map)
        needs_correction = (
            (val_result.math_result.status == "mismatched" and doc_type is DocType.INVOICE)
            or (math_decision == MathCheckDecision.SKIP_FIELDS_MISSING and doc_type is DocType.INVOICE)
        )
        correction_reason = (
            val_result.math_result.reason
            if val_result.math_result.status == "mismatched"
            else "Required invoice math fields (subtotal, tax_amount, total_amount) not all found — re-extract"
        )

        if needs_correction:
            logger.info("Self-Correction Loop triggered for document %s: %s", document_id, correction_reason)
            corrected_candidates, corrected_payload, correction_note = (
                field_extractor.extract_fields_with_correction(
                    text,
                    doc_type,
                    payload,
                    correction_reason,
                    ocr_quality,
                )
            )
            # Re-validate with corrected candidates
            corrected_val_result = validation.validate(corrected_candidates, doc_type)
            s3_ms = int((time.perf_counter() - s3_start) * 1000)
            
            with get_db_session() as session:
                log_audit(
                    session,
                    document_id,
                    "SELF_CORRECTION_ATTEMPT_2",
                    json.dumps({
                        "previous_error": correction_reason,
                        "correction_note": correction_note,
                        "corrected_payload": corrected_payload,
                        "resolved": not corrected_val_result.has_errors,
                    }, default=str),
                    run_number=run_number,
                    elapsed_ms=s3_ms,
                )
                
            # If self-correction resolved the issue or improved outcome, adopt it
            if not corrected_val_result.has_errors or len(corrected_val_result.issues) < len(val_result.issues):
                candidates = corrected_candidates
                val_result = corrected_val_result
                self_corrected = True
        else:
            s3_ms = int((time.perf_counter() - s3_start) * 1000)

        issues = [issue.as_dict() for issue in val_result.issues]

        # Stage 4: Smart Routing & AI Compliance Auditor Agent
        s4_start = time.perf_counter()
        confidence = routing.overall_confidence(val_result.candidates, class_conf)
        status = routing.route(confidence, val_result.has_errors)

        audit_summary_text = auditor.generate_audit_summary(
            doc_type=doc_type,
            overall_confidence=confidence,
            status=status,
            math_result=val_result.math_result,
            issues=val_result.issues,
        )
        s4_ms = int((time.perf_counter() - s4_start) * 1000)

        # Persist final state in scoped DB session
        with get_db_session() as session:
            doc = session.get(Document, document_id)
            if not doc:
                return PipelineOutcome(status=DocStatus.FAILED, confidence=0.0, issues=issues)
            
            doc.overall_confidence = confidence
            doc.status = status
            doc.validation_errors = json.dumps(issues)
            doc.audit_summary = audit_summary_text
            total_elapsed_ms = int((time.perf_counter() - started) * 1000)
            doc.processing_ms = total_elapsed_ms

            # Refresh extracted fields
            doc.fields.clear()
            session.flush()

            error_keys = {
                k for issue in val_result.issues if issue.severity == "error" for k in issue.fields
            }
            for candidate in val_result.candidates:
                session.add(
                    ExtractedField(
                        document_id=document_id,
                        field_key=candidate.field_key,
                        field_value=candidate.field_value,
                        confidence_score=candidate.confidence_score,
                        is_validated=candidate.field_key not in error_keys,
                        bbox=candidate.bbox,
                    )
                )

            log_audit(
                session,
                document_id,
                "AGENT_AUDITOR",
                json.dumps({
                    "audit_summary": audit_summary_text,
                    "math_status": val_result.math_result.status,
                    "math_delta": val_result.math_result.delta,
                }),
                run_number=run_number,
                elapsed_ms=s4_ms,
            )
            log_audit(
                session,
                document_id,
                f"ROUTED_{status.value}",
                json.dumps({
                    "overall_confidence": confidence,
                    "status": status.value,
                    "rule_failures": len(error_keys),
                    "self_corrected": self_corrected,
                    "total_ms": total_elapsed_ms,
                }),
                run_number=run_number,
                elapsed_ms=total_elapsed_ms,
            )

        # Refresh the caller's instance if session is active
        try:
            if db is not None and db.is_active:
                db.refresh(document)
        except Exception:
            pass

        return PipelineOutcome(
            status=status,
            confidence=confidence,
            issues=issues,
            audit_summary=audit_summary_text,
            self_corrected=self_corrected,
        )

    except Exception as exc:  # noqa: BLE001 - Pipeline must degrade gracefully
        logger.exception("Pipeline failed for document %s: %s", document_id, exc)
        with get_db_session() as session:
            doc = session.get(Document, document_id)
            if doc:
                doc.status = DocStatus.ACTION_REQUIRED
                fail_ms = int((time.perf_counter() - started) * 1000)
                doc.processing_ms = fail_ms
                err_issue = [
                    {"rule": "pipeline_error", "message": str(exc), "severity": "error", "fields": []}
                ]
                doc.validation_errors = json.dumps(err_issue)
                doc.audit_summary = f"Pipeline degraded: {exc}. Routed to ACTION_REQUIRED for human review."
                log_audit(
                    session,
                    document_id,
                    "PIPELINE_DEGRADED",
                    str(exc),
                    run_number=run_number,
                    elapsed_ms=fail_ms,
                )
        
        try:
            if db is not None and db.is_active:
                db.refresh(document)
        except Exception:
            pass

        return PipelineOutcome(
            status=DocStatus.ACTION_REQUIRED,
            confidence=0.3,
            issues=[{"rule": "pipeline_error", "message": str(exc), "severity": "error", "fields": []}],
            audit_summary=f"Pipeline error: {exc}. Routed to ACTION_REQUIRED.",
        )


def execute_document_pipeline(document_id: str) -> PipelineOutcome:
    """Safe runner for BackgroundTasks: opens its own scoped database session."""
    with get_db_session() as session:
        doc = session.get(Document, document_id)
        if not doc:
            return PipelineOutcome(status=DocStatus.FAILED, confidence=0.0, issues=[])
        return process_document_sync(session, doc)


async def process_document(db: Session, document: Document) -> PipelineOutcome:
    """Async wrapper so LLM/OCR/CPU work never blocks the event loop."""
    return await asyncio.to_thread(process_document_sync, db, document)
