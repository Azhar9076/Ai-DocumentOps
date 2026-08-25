"""Async orchestration of the document processing pipeline."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import AuditLog, DocStatus, Document, ExtractedField
from app.pipeline import classifier, docling_parser, routing, validation
from app.pipeline.schemas_extraction import FieldCandidate, SCHEMA_BY_TYPE
from app.services import granite_service, governance_service

logger = logging.getLogger(__name__)

PIPELINE_STEPS = [
    "Uploaded",
    "IBM Docling Parsing",
    "Classified",
    "IBM Granite Extraction",
    "Validating Rules",
    "Complete",
]


@dataclass
class PipelineOutcome:
    status: DocStatus
    confidence: float
    issues: list[dict[str, object]]


def log_audit(
    db: Session, document_id: str, action: str, details: str, performed_by: str = "system"
) -> None:
    db.add(
        AuditLog(
            document_id=document_id, action=action, details=details, performed_by=performed_by
        )
    )


def process_document_sync(db: Session, document: Document) -> PipelineOutcome:
    """Run the full pipeline for a persisted document record."""
    started = time.perf_counter()
    document.status = DocStatus.PROCESSING
    log_audit(db, document.id, "PIPELINE_STARTED", "Pipeline execution started")
    db.commit()

    try:
        # Use IBM Docling for document parsing
        text, page_count, docling_quality = docling_parser.parse_document(Path(document.file_path))
        document.raw_text = text[:200_000]
        document.page_count = page_count
        log_audit(
            db,
            document.id,
            "DOCLING_PARSED",
            json.dumps({"chars": len(text), "pages": page_count, "docling_quality": docling_quality}),
        )

        doc_type, classification_confidence = classifier.classify(text)
        document.doc_type = doc_type
        log_audit(
            db,
            document.id,
            "CLASSIFIED",
            json.dumps({"doc_type": doc_type.value, "confidence": classification_confidence}),
        )

        # Use IBM Granite for field extraction
        schema_cls = SCHEMA_BY_TYPE.get(doc_type.value)
        schema_fields = list(schema_cls.model_fields.keys()) if schema_cls else []
        
        granite_result = granite_service.extract_fields_with_granite(text, doc_type.value, schema_fields)
        
        # Convert Granite results to FieldCandidate format
        candidates = []
        for field_key, field_data in granite_result.items():
            candidates.append(
                FieldCandidate(
                    field_key=field_key,
                    field_value=field_data.get("value", ""),
                    confidence_score=field_data.get("confidence", 0.0),
                    bbox=None  # Granite doesn't provide bbox
                )
            )
        
        log_audit(
            db,
            document.id,
            "GRANITE_EXTRACTED",
            json.dumps({"count": len(candidates), "model": granite_service.get_model_info()["model"]}, default=str),
        )

        result = validation.validate(candidates, doc_type)
        issues = [issue.as_dict() for issue in result.issues]
        document.validation_errors = json.dumps(issues)
        log_audit(db, document.id, "RULES_VALIDATED", json.dumps({"issues": issues, "has_errors": result.has_errors}))

        confidence = routing.overall_confidence(result.candidates, classification_confidence)
        status = routing.route(confidence, result.has_errors)
        document.overall_confidence = confidence
        document.status = status

        document.fields.clear()
        db.flush()
        error_keys = {k for issue in result.issues if issue.severity == "error" for k in issue.fields}
        
        # Get IBM stack version for tracking
        ibm_stack_info = granite_service.get_model_info()
        document.ibm_stack_version = f"docling-1.0+{ibm_stack_info['model']}"
        
        for candidate in result.candidates:
            # Extract context snippet for lineage
            context_snippet = docling_parser.extract_lineage_context(text, candidate.field_key)
            
            # Determine extraction method based on confidence
            extraction_method = "ibm-granite" if candidate.confidence_score > 0.8 else "hybrid"
            
            db.add(
                ExtractedField(
                    document_id=document.id,
                    field_key=candidate.field_key,
                    field_value=candidate.field_value,
                    confidence_score=candidate.confidence_score,
                    is_validated=candidate.field_key not in error_keys,
                    bbox=candidate.bbox,
                    extraction_method=extraction_method,
                    context_snippet=context_snippet,
                )
            )

        document.processing_ms = int((time.perf_counter() - started) * 1000)
        log_audit(
            db,
            document.id,
            f"ROUTED_{status.value}",
            json.dumps({"overall_confidence": confidence, "rule_failures": len(error_keys)}),
        )
        db.commit()
        return PipelineOutcome(status=status, confidence=confidence, issues=issues)
    except Exception as exc:  # noqa: BLE001 - pipeline must never crash the API
        db.rollback()
        logger.exception("Pipeline failed for document %s", document.id)
        document.status = DocStatus.FAILED
        document.processing_ms = int((time.perf_counter() - started) * 1000)
        document.validation_errors = json.dumps(
            [{"rule": "pipeline_error", "message": str(exc), "severity": "error", "fields": []}]
        )
        log_audit(db, document.id, "PIPELINE_FAILED", str(exc))
        db.commit()
        return PipelineOutcome(
            status=DocStatus.FAILED, confidence=0.0, issues=json.loads(document.validation_errors)
        )


async def process_document(db: Session, document: Document) -> PipelineOutcome:
    """Async wrapper so OCR/CPU work never blocks the event loop."""
    return await asyncio.to_thread(process_document_sync, db, document)
