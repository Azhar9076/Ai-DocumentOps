import io
from typing import Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
)
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.config import save_routing_thresholds, settings
from app.db import get_db
from app.models import DocStatus, Document
from app.pipeline.runner import (
    PIPELINE_STEPS,
    execute_document_pipeline,
    process_document,
)
from app.pipeline.watsonx import budget_guard
from app.schemas import (
    AuditLogOut,
    BenchmarkRunOut,
    BulkReviewSubmission,
    DocumentDetail,
    DocumentSummary,
    FieldCorrection,
    MetricsOut,
    QualityOut,
    ReviewSubmission,
    RoutingThresholds,
)
from app.services import analytics
from app.services import documents as doc_service

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "AI DocumentOps", "model": "IBM Granite 3.0 via watsonx.ai"}


@router.get("/pipeline/steps")
def pipeline_steps() -> dict[str, list[str]]:
    return {"steps": PIPELINE_STEPS}


@router.post("/documents", response_model=DocumentDetail, status_code=201)
async def upload_document(
    file: UploadFile = File(...), db: Session = Depends(get_db)
) -> DocumentDetail:
    document = doc_service.store_upload(db, file.filename or "document", file.content_type or "", file.file)
    await process_document(db, document)
    db.refresh(document)
    return doc_service.to_detail(document)


@router.get("/documents", response_model=list[DocumentSummary])
def list_documents(
    status: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
) -> list[DocumentSummary]:
    if status and status not in DocStatus.__members__:
        raise HTTPException(status_code=400, detail=f"Unknown status '{status}'")
    return [
        DocumentSummary.model_validate(d, from_attributes=True)
        for d in doc_service.list_documents(db, status=status, limit=limit)
    ]


@router.get("/documents/{document_id}", response_model=DocumentDetail)
def get_document(document_id: str, db: Session = Depends(get_db)) -> DocumentDetail:
    return doc_service.to_detail(doc_service.get_document(db, document_id))


@router.get("/documents/{document_id}/file")
def get_document_file(document_id: str, db: Session = Depends(get_db)) -> FileResponse:
    document = doc_service.get_document(db, document_id)
    return FileResponse(
        document.file_path,
        media_type=document.mime_type or None,
        headers={"content-disposition": f'inline; filename="{document.filename}"'},
    )


@router.get("/documents/{document_id}/audit", response_model=list[AuditLogOut])
def get_audit_trail(document_id: str, db: Session = Depends(get_db)) -> list[AuditLogOut]:
    document = doc_service.get_document(db, document_id)
    return [AuditLogOut.model_validate(log, from_attributes=True) for log in document.audit_logs]


@router.post("/documents/{document_id}/review", response_model=DocumentDetail)
def review_document(
    document_id: str, submission: ReviewSubmission, db: Session = Depends(get_db)
) -> DocumentDetail:
    document = doc_service.get_document(db, document_id)
    return doc_service.to_detail(doc_service.submit_review(db, document, submission))


@router.post("/documents/{document_id}/correct")
def correct_document_field(
    document_id: str, correction: FieldCorrection, db: Session = Depends(get_db)
) -> dict[str, Any]:
    """One-click Approve & Learn endpoint: update field, log review, and feed benchmark cache."""
    return doc_service.correct_field(db, document_id, correction)


@router.post("/documents/{document_id}/reprocess", response_model=DocumentDetail)
async def reprocess_document(document_id: str, db: Session = Depends(get_db)) -> DocumentDetail:
    document = doc_service.get_document(db, document_id)
    await process_document(db, document)
    db.refresh(document)
    return doc_service.to_detail(document)


@router.post("/documents/{document_id}/cancel", response_model=DocumentDetail)
def cancel_document_pipeline(document_id: str, db: Session = Depends(get_db)) -> DocumentDetail:
    document = doc_service.cancel_document(db, document_id)
    return doc_service.to_detail(document)


@router.post("/documents/bulk-review", response_model=list[DocumentSummary])
def bulk_review_documents(
    submission: BulkReviewSubmission, db: Session = Depends(get_db)
) -> list[DocumentSummary]:
    updated = doc_service.bulk_review(db, submission)
    return [DocumentSummary.model_validate(d, from_attributes=True) for d in updated]


@router.get("/documents/{document_id}/export")
def export_document(
    document_id: str, format: str = Query(default="json"), db: Session = Depends(get_db)
) -> Response:
    document = doc_service.get_document(db, document_id)
    if format.lower() == "csv":
        csv_data = doc_service.export_document_csv(document)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{document.id}_audit_export.csv"'},
        )
    json_data = doc_service.export_document_json(document)
    return JSONResponse(content=json_data)


@router.get("/documents/{document_id}/export-audit")
def export_audit_certificate(
    document_id: str, format: str = Query(default="pdf"), db: Session = Depends(get_db)
) -> Response:
    """Export formal Document Compliance & Audit Certificate in PDF or CSV format."""
    document = doc_service.get_document(db, document_id)
    if format.lower() == "csv":
        csv_data = doc_service.export_document_csv(document)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{document.id}_compliance_audit.csv"'},
        )
    pdf_bytes = doc_service.generate_audit_pdf(document)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{document.id}_compliance_certificate.pdf"'},
    )


@router.get("/metrics", response_model=MetricsOut)
def metrics(db: Session = Depends(get_db)) -> MetricsOut:
    return analytics.build_metrics(db)


@router.get("/quality", response_model=QualityOut)
def quality(
    refresh: bool = Query(default=False),
    compare: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> QualityOut:
    return analytics.build_quality(db, refresh_benchmark=refresh, compare=compare)


@router.post("/quality/benchmark")
def trigger_benchmark(db: Session = Depends(get_db)) -> QualityOut:
    """Manually trigger a fresh run of the 18-sample benchmark loop."""
    return analytics.build_quality(db, refresh_benchmark=True)


@router.get("/admin/thresholds", response_model=RoutingThresholds)
def get_thresholds() -> RoutingThresholds:
    return RoutingThresholds(
        auto_approved_min=settings.auto_approve_threshold,
        needs_review_min=settings.review_threshold,
    )


@router.put("/admin/thresholds", response_model=RoutingThresholds)
def update_thresholds(payload: RoutingThresholds) -> RoutingThresholds:
    save_routing_thresholds(payload.auto_approved_min, payload.needs_review_min)
    return RoutingThresholds(
        auto_approved_min=settings.auto_approve_threshold,
        needs_review_min=settings.review_threshold,
    )


@router.post("/demo/stress-test")
async def run_stress_test(
    background_tasks: BackgroundTasks,
    sample_count: int = Query(default=5, ge=1, le=10),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Concurrent intake simulation: generate N sample documents, route via background tasks, and guard budget."""
    samples = doc_service.get_demo_sample_documents(limit=sample_count)
    job_ids = []
    for filename, mime, buffer in samples:
        doc = doc_service.store_upload(db, filename, mime, io.BytesIO(buffer))
        background_tasks.add_task(execute_document_pipeline, doc.id)
        job_ids.append(doc.id)
    return {
        "job_ids": job_ids,
        "started": len(job_ids),
        "budget_remaining": budget_guard.remaining,
        "max_calls": budget_guard.max_calls,
    }


@router.get("/demo/stress-test/status", response_model=list[DocumentSummary])
def get_stress_test_status(
    job_ids: str = Query(default=""), db: Session = Depends(get_db)
) -> list[DocumentSummary]:
    """Retrieve live processing status for batch-submitted documents."""
    id_list = [j.strip() for j in job_ids.split(",") if j.strip()]
    if not id_list:
        docs = doc_service.list_documents(db, limit=10)
    else:
        docs = []
        for jid in id_list:
            d = db.get(Document, jid)
            if d:
                docs.append(d)
    return [DocumentSummary.model_validate(d, from_attributes=True) for d in docs]
