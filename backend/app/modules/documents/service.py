from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import Document, DocumentStatus
from backend.app.modules.common.text import sanitize_metadata, sanitize_text
from backend.app.modules.documents.schemas import DocumentCreate


class DocumentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_document(self, payload: DocumentCreate) -> Document:
        document = Document(
            filename=sanitize_text(payload.filename).strip() or "upload.txt",
            content_type=sanitize_text(payload.content_type).strip() or "application/octet-stream",
            source_type=payload.source_type,
            status=DocumentStatus.pending,
            metadata_json=sanitize_metadata(payload.metadata),
        )
        self.session.add(document)
        await self.session.commit()
        await self.session.refresh(document)
        return document

    async def get_document(self, document_id: UUID | str) -> Document | None:
        if isinstance(document_id, str):
            document_id = UUID(document_id)
        return await self.session.get(Document, document_id)
