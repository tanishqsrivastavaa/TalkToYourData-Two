from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import get_settings
from backend.app.db.models import Document, DocumentChunk, DocumentStatus
from backend.app.modules.providers.embeddings import EmbeddingProvider, get_embedding_provider


@dataclass(slots=True)
class ReindexResult:
    chunks_reindexed: int = 0
    documents_touched: int = 0


class EmbeddingMaintenanceService:
    def __init__(
        self,
        session: AsyncSession,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        self.session = session
        self.settings = get_settings()
        self.embedding_provider = embedding_provider or get_embedding_provider(self.settings)

    async def reindex_stale_embeddings(self, batch_size: int = 100) -> ReindexResult:
        result = ReindexResult()
        touched_document_ids: set = set()

        while True:
            chunks = await self._get_stale_chunks(limit=batch_size)
            if not chunks:
                break

            embeddings = await self.embedding_provider.embed_texts([chunk.text for chunk in chunks])
            for chunk, embedding in zip(chunks, embeddings, strict=False):
                chunk.embedding = embedding
                touched_document_ids.add(chunk.document_id)

            result.chunks_reindexed += len(chunks)
            await self.session.commit()

        if touched_document_ids:
            documents = (
                await self.session.execute(
                    select(Document).where(Document.id.in_(touched_document_ids))
                )
            ).scalars().all()
            for document in documents:
                document.status = DocumentStatus.indexed
            await self.session.commit()

        result.documents_touched = len(touched_document_ids)
        return result

    async def count_stale_chunks(self) -> int:
        chunks = await self._get_stale_chunks(limit=None)
        return len(chunks)

    async def _get_stale_chunks(self, limit: int | None) -> list[DocumentChunk]:
        statement = select(DocumentChunk).order_by(DocumentChunk.created_at, DocumentChunk.chunk_index)
        if limit is not None:
            statement = statement.limit(limit)
        chunks = (await self.session.execute(statement)).scalars().all()
        return [chunk for chunk in chunks if self._is_stale_embedding(chunk.embedding, self.settings.embedding_dimension)]

    @staticmethod
    def _is_stale_embedding(embedding: list[float], expected_dimension: int) -> bool:
        if len(embedding) != expected_dimension:
            return True
        return any(not isfinite(value) for value in embedding)
