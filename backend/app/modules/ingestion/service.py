from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import get_settings
from backend.app.db.models import DocumentChunk, DocumentStatus
from backend.app.modules.documents.schemas import DocumentCreate
from backend.app.modules.documents.service import DocumentService
from backend.app.modules.ingestion.chunking import SemanticChunker
from backend.app.modules.ingestion.parsers import ParserRegistry, infer_source_type
from backend.app.modules.providers.embeddings import EmbeddingProvider, get_embedding_provider


class IngestionService:
    def __init__(
        self,
        session: AsyncSession,
        embedding_provider: EmbeddingProvider | None = None,
        parser_registry: ParserRegistry | None = None,
    ) -> None:
        settings = get_settings()
        self.session = session
        self.document_service = DocumentService(session)
        self.embedding_provider = embedding_provider or get_embedding_provider(settings)
        self.parser_registry = parser_registry or ParserRegistry()
        self.chunker = SemanticChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

    async def ingest_upload(self, filename: str, content_type: str, file_bytes: bytes):
        source_type = infer_source_type(filename, content_type)
        document = await self.document_service.create_document(
            DocumentCreate(
                filename=filename,
                content_type=content_type,
                source_type=source_type,
            )
        )

        document.status = DocumentStatus.processing
        await self.session.commit()

        parser = self.parser_registry.get(source_type)
        parsed = await parser.parse(file_bytes=file_bytes, filename=filename)
        chunks = self.chunker.split(parsed.text, metadata=parsed.metadata)
        embeddings = await self.embedding_provider.embed_texts([chunk.text for chunk in chunks])

        for chunk, embedding in zip(chunks, embeddings, strict=False):
            self.session.add(
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=chunk.chunk_index,
                    text=chunk.text,
                    section_title=str(chunk.metadata.get("section_title")) if chunk.metadata.get("section_title") else None,
                    page_number=int(chunk.metadata["page_number"]) if "page_number" in chunk.metadata else None,
                    token_count=chunk.token_count,
                    metadata_json=chunk.metadata,
                    embedding=embedding,
                )
            )

        document.status = DocumentStatus.indexed
        document.metadata_json = parsed.metadata
        await self.session.commit()
        await self.session.refresh(document)
        return document
