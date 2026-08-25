from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import DocStatus
from app.pipeline.runner import PIPELINE_STEPS, process_document
from app.schemas import (
    AuditLogOut,
    DocumentDetail,
    DocumentSummary,
    MetricsOut,
    QualityOut,
    ReviewSubmission,
)
from app.services import analytics
from app.services import documents as doc_service

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


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


@router.post("/documents/{document_id}/reprocess", response_model=DocumentDetail)
async def reprocess_document(document_id: str, db: Session = Depends(get_db)) -> DocumentDetail:
    document = doc_service.get_document(db, document_id)
    await process_document(db, document)
    db.refresh(document)
    return doc_service.to_detail(document)


@router.get("/metrics", response_model=MetricsOut)
def metrics(db: Session = Depends(get_db)) -> MetricsOut:
    return analytics.build_metrics(db)


@router.get("/quality", response_model=QualityOut)
def quality(db: Session = Depends(get_db)) -> QualityOut:
    return analytics.build_quality(db)
