from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_session
from backend.app.modules.documents.schemas import DocumentRead, UploadResponse
from backend.app.modules.documents.service import DocumentService
from backend.app.modules.ingestion.service import IngestionService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
) -> UploadResponse:
    contents = await file.read()
    service = IngestionService(session)
    document = await service.ingest_upload(
        filename=file.filename or "upload.txt",
        content_type=file.content_type or "text/plain",
        file_bytes=contents,
    )
    return UploadResponse(
        status="success",
        document_id=document.id,
        message="Document indexed successfully",
    )


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(
    document_id: str,
    session: AsyncSession = Depends(get_session),
) -> DocumentRead:
    service = DocumentService(session)
    document = await service.get_document(document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DocumentRead.model_validate(document)
