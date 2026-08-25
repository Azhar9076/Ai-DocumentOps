"""Governance service for compliance audit logs and lineage tracking."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import AuditLog, Document, DocStatus, ExtractedField
from app.services import granite_service

logger = logging.getLogger(__name__)


def log_system_event(
    db: Session,
    document_id: str,
    action: str,
    details: dict[str, Any],
    performed_by: str = "system"
) -> AuditLog:
    """Log a system event to the audit trail."""
    audit_log = AuditLog(
        document_id=document_id,
        action=action,
        performed_by=performed_by,
        timestamp=datetime.now(timezone.utc),
        details=json.dumps(details)
    )
    db.add(audit_log)
    db.commit()
    return audit_log


def get_document_lineage(db: Session, document_id: str) -> dict[str, Any]:
    """
    Get complete lineage information for a document.
    Includes processing history, field extraction context, and model information.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        return {"error": "Document not found"}
    
    # Get audit logs
    audit_logs = db.query(AuditLog).filter(
        AuditLog.document_id == document_id
    ).order_by(AuditLog.timestamp).all()
    
    # Get fields with lineage context
    fields = db.query(ExtractedField).filter(
        ExtractedField.document_id == document_id
    ).all()
    
    # Build lineage information
    lineage = {
        "document_id": document_id,
        "document_type": document.doc_type.value,
        "processing_timeline": [
            {
                "timestamp": log.timestamp.isoformat(),
                "action": log.action,
                "performed_by": log.performed_by,
                "details": json.loads(log.details) if log.details else {}
            }
            for log in audit_logs
        ],
        "field_lineage": [
            {
                "field_key": field.field_key,
                "field_value": field.field_value,
                "confidence_score": field.confidence_score,
                "extraction_method": "ibm-granite" if field.confidence_score > 0.8 else "hybrid",
                "bbox": field.bbox,
                "is_validated": field.is_validated
            }
            for field in fields
        ],
        "model_info": granite_service.get_model_info(),
        "processing_metadata": {
            "overall_confidence": document.overall_confidence,
            "processing_time_ms": document.processing_ms,
            "page_count": document.page_count,
            "status": document.status.value
        }
    }
    
    return lineage


def get_field_context(db: Session, document_id: str, field_key: str) -> dict[str, Any]:
    """
    Get specific context and lineage for a single field.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        return {"error": "Document not found"}
    
    field = db.query(ExtractedField).filter(
        ExtractedField.document_id == document_id,
        ExtractedField.field_key == field_key
    ).first()
    
    if not field:
        return {"error": "Field not found"}
    
    # Extract context from document text using Docling parser
    from app.pipeline.docling_parser import extract_lineage_context
    context_snippet = extract_lineage_context(document.raw_text, field_key)
    
    return {
        "field_key": field.field_key,
        "field_value": field.field_value,
        "confidence_score": field.confidence_score,
        "extraction_context": context_snippet,
        "bbox": field.bbox,
        "is_validated": field.is_validated,
        "extraction_method": "ibm-granite" if field.confidence_score > 0.8 else "hybrid"
    }


def get_system_governance_report(db: Session) -> dict[str, Any]:
    """
    Generate a comprehensive governance report for the system.
    """
    # Get document counts by status
    status_counts = db.query(
        Document.status,
        func.count(Document.id)
    ).group_by(Document.status).all()
    
    # Get average confidence scores
    avg_confidence = db.query(
        func.avg(Document.overall_confidence)
    ).scalar() or 0.0
    
    # Get total processing time
    total_processing = db.query(
        func.sum(Document.processing_ms)
    ).scalar() or 0
    
    # Get audit log statistics
    total_audit_logs = db.query(func.count(AuditLog.id)).scalar()
    
    # Get model information
    model_info = granite_service.get_model_info()
    
    return {
        "report_generated_at": datetime.now(timezone.utc).isoformat(),
        "model_stack": {
            "document_parser": "IBM Docling",
            "llm_provider": model_info["provider"],
            "llm_model": model_info["model"],
            "llm_status": model_info["status"]
        },
        "processing_statistics": {
            "total_documents": db.query(func.count(Document.id)).scalar(),
            "status_breakdown": {status.value: count for status, count in status_counts},
            "average_confidence": round(float(avg_confidence), 4),
            "total_processing_time_ms": int(total_processing),
            "average_processing_time_ms": round(int(total_processing / max(1, db.query(func.count(Document.id)).scalar())), 2)
        },
        "audit_statistics": {
            "total_audit_entries": total_audit_logs,
            "compliance_rate": _calculate_compliance_rate(db)
        },
        "system_health": {
            "ibm_integration_active": model_info["status"] == "active",
            "fallback_mode_active": model_info["status"] == "fallback-mode"
        }
    }


def _calculate_compliance_rate(db: Session) -> float:
    """Calculate the overall compliance rate based on validation results."""
    total = db.query(func.count(Document.id)).scalar()
    if total == 0:
        return 0.0
    
    # Count documents that passed validation (auto-approved or approved)
    compliant = db.query(func.count(Document.id)).filter(
        Document.status.in_([DocStatus.AUTO_APPROVED, DocStatus.APPROVED])
    ).scalar()
    
    return round(compliant / total * 100, 2)


def track_field_edit(
    db: Session,
    document_id: str,
    field_key: str,
    original_value: str,
    new_value: str,
    user_id: str
) -> None:
    """
    Track when a human user edits a field value.
    This is important for governance and audit trails.
    """
    log_system_event(
        db=db,
        document_id=document_id,
        action="FIELD_EDITED",
        details={
            "field_key": field_key,
            "original_value": original_value,
            "new_value": new_value,
            "edit_reason": "human_correction"
        },
        performed_by=user_id
    )


def get_ibm_stack_info() -> dict[str, Any]:
    """Get current IBM stack information and versions."""
    try:
        import docling
        docling_version = getattr(docling, "__version__", "unknown")
    except ImportError:
        docling_version = "not installed"
    
    try:
        import ibm_watsonx_ai
        watsonx_version = getattr(ibm_watsonx_ai, "__version__", "unknown")
    except ImportError:
        watsonx_version = "not installed"
    
    model_info = granite_service.get_model_info()
    
    return {
        "docling": {
            "installed": docling_version != "not installed",
            "version": docling_version,
            "status": "active" if docling_version != "not installed" else "fallback"
        },
        "watsonx_ai": {
            "installed": watsonx_version != "not installed",
            "version": watsonx_version,
            "status": model_info["status"]
        },
        "granite_model": {
            "model_id": model_info["model"],
            "provider": model_info["provider"],
            "deployment": model_info["deployment_id"]
        },
        "overall_status": "operational" if (
            docling_version != "not installed" and 
            model_info["status"] == "active"
        ) else "degraded"
    }