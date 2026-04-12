from __future__ import annotations

import re
from typing import Any

from sqlalchemy import inspect
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import get_settings
from backend.app.db.models import DocumentChunk
from backend.app.modules.providers.embeddings import EmbeddingProvider, get_embedding_provider
from backend.app.modules.queries.schemas import QueryPlan
from backend.app.modules.retrieval.rerank import FusionReranker
from backend.app.modules.retrieval.schemas import RetrievalCandidate


class HybridRetrievalService:
    def __init__(
        self,
        session: AsyncSession,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        self.session = session
        self.settings = get_settings()
        self.reranker = FusionReranker()
        self.embedding_provider = embedding_provider or get_embedding_provider(self.settings)

    async def retrieve(self, plan: QueryPlan) -> list[RetrievalCandidate]:
        query_text = " ".join(plan.sub_queries) or ""
        query_vector = (await self.embedding_provider.embed_texts([query_text]))[0]
        if not await self._supports_postgres_hybrid_search():
            return await self._retrieve_fallback(plan, query_text, query_vector)

        merged_candidates = self._merge_candidates(
            await self._run_vector_search(plan, query_vector),
            await self._run_keyword_search(plan, query_text),
            await self._run_metadata_search(plan, query_text),
        )
        return self.reranker.rank(merged_candidates)[: self.settings.max_retrieved_chunks]

    async def _run_vector_search(
        self,
        plan: QueryPlan,
        query_vector: list[float],
    ) -> list[RetrievalCandidate]:
        filters = self._build_filter_clause(plan)
        statement = text(
            f"""
            SELECT
                id AS chunk_id,
                document_id,
                text,
                section_title,
                page_number,
                GREATEST(0.0, 1 - (embedding_vector <=> CAST(:query_vector AS vector))) AS vector_score,
                0.0 AS keyword_score,
                0.0 AS metadata_score
            FROM document_chunks
            WHERE embedding_vector IS NOT NULL {filters}
            ORDER BY embedding_vector <=> CAST(:query_vector AS vector)
            LIMIT :limit
            """
        )
        params = self._filter_params(plan) | {
            "query_vector": self._vector_literal(query_vector),
            "limit": self.settings.max_retrieved_chunks,
        }
        return await self._execute_candidates(statement, params)

    async def _run_keyword_search(self, plan: QueryPlan, query_text: str) -> list[RetrievalCandidate]:
        filters = self._build_filter_clause(plan)
        statement = text(
            f"""
            SELECT
                id AS chunk_id,
                document_id,
                text,
                section_title,
                page_number,
                0.0 AS vector_score,
                ts_rank_cd(search_vector, websearch_to_tsquery('english', :query_text)) AS keyword_score,
                0.0 AS metadata_score
            FROM document_chunks
            WHERE search_vector @@ websearch_to_tsquery('english', :query_text) {filters}
            ORDER BY keyword_score DESC
            LIMIT :limit
            """
        )
        params = self._filter_params(plan) | {"query_text": query_text, "limit": self.settings.max_retrieved_chunks}
        return await self._execute_candidates(statement, params)

    async def _run_metadata_search(self, plan: QueryPlan, query_text: str) -> list[RetrievalCandidate]:
        filters = self._build_filter_clause(plan)
        statement = text(
            f"""
            SELECT
                id AS chunk_id,
                document_id,
                text,
                section_title,
                page_number,
                0.0 AS vector_score,
                0.0 AS keyword_score,
                CASE
                    WHEN section_title ILIKE :section_pattern THEN 1.0
                    WHEN CAST(page_number AS TEXT) = :page_number THEN 0.9
                    ELSE 0.5
                END AS metadata_score
            FROM document_chunks
            WHERE (
                section_title ILIKE :section_pattern
                OR CAST(page_number AS TEXT) = :page_number
                OR metadata_json ->> 'filename' ILIKE :filename_pattern
            ) {filters}
            ORDER BY metadata_score DESC, chunk_index ASC
            LIMIT :limit
            """
        )
        params = self._filter_params(plan) | {
            "section_pattern": f"%{query_text[:100]}%",
            "filename_pattern": f"%{query_text[:100]}%",
            "page_number": self._extract_page_number(query_text),
            "limit": self.settings.max_retrieved_chunks,
        }
        return await self._execute_candidates(statement, params)

    async def _execute_candidates(self, statement: Any, params: dict[str, Any]) -> list[RetrievalCandidate]:
        rows = (await self.session.execute(statement, params)).mappings().all()
        return [RetrievalCandidate.model_validate(dict(row)) for row in rows]

    async def _retrieve_fallback(
        self,
        plan: QueryPlan,
        query_text: str,
        query_vector: list[float],
    ) -> list[RetrievalCandidate]:
        statement = select(DocumentChunk).order_by(DocumentChunk.chunk_index)
        if plan.document_ids:
            statement = statement.where(DocumentChunk.document_id.in_(plan.document_ids))

        chunks = (await self.session.execute(statement)).scalars().all()
        query_terms = self._tokenize(query_text)
        page_number = self._extract_page_number(query_text)
        candidates: list[RetrievalCandidate] = []

        for chunk in chunks:
            keyword_score = self._keyword_overlap_score(query_terms, chunk.text)
            metadata_score = self._metadata_match_score(chunk, query_text, page_number)
            vector_score = self._cosine_similarity(query_vector, chunk.embedding)
            if max(vector_score, keyword_score, metadata_score) <= 0:
                continue

            candidates.append(
                RetrievalCandidate(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    text=chunk.text,
                    section_title=chunk.section_title,
                    page_number=chunk.page_number,
                    vector_score=vector_score,
                    keyword_score=keyword_score,
                    metadata_score=metadata_score,
                )
            )

        return self.reranker.rank(candidates)[: self.settings.max_retrieved_chunks]

    def _merge_candidates(self, *candidate_lists: list[RetrievalCandidate]) -> list[RetrievalCandidate]:
        merged: dict[Any, RetrievalCandidate] = {}
        for candidate_list in candidate_lists:
            for candidate in candidate_list:
                existing = merged.get(candidate.chunk_id)
                if existing is None:
                    merged[candidate.chunk_id] = candidate
                    continue
                existing.vector_score = max(existing.vector_score, candidate.vector_score)
                existing.keyword_score = max(existing.keyword_score, candidate.keyword_score)
                existing.metadata_score = max(existing.metadata_score, candidate.metadata_score)
        return list(merged.values())

    def _build_filter_clause(self, plan: QueryPlan) -> str:
        if not plan.document_ids:
            return ""
        return " AND document_id = ANY(CAST(:document_ids AS uuid[]))"

    def _filter_params(self, plan: QueryPlan) -> dict[str, Any]:
        if not plan.document_ids:
            return {}
        return {"document_ids": [str(document_id) for document_id in plan.document_ids]}

    def _vector_literal(self, values: list[float]) -> str:
        return "[" + ",".join(f"{value:.8f}" for value in values) + "]"

    def _extract_page_number(self, query_text: str) -> str:
        match = re.search(r"\bpage\s+(\d+)\b", query_text.lower())
        return match.group(1) if match else ""

    async def _supports_postgres_hybrid_search(self) -> bool:
        if self.session.bind is None or self.session.bind.dialect.name != "postgresql":
            return False

        async with self.session.bind.connect() as conn:
            return await conn.run_sync(self._sync_supports_postgres_hybrid_search)

    @staticmethod
    def _sync_supports_postgres_hybrid_search(sync_conn: Any) -> bool:
        inspector = inspect(sync_conn)
        if "document_chunks" not in inspector.get_table_names():
            return False
        column_names = {column["name"] for column in inspector.get_columns("document_chunks")}
        return {"embedding_vector", "search_vector"}.issubset(column_names)

    @staticmethod
    def _tokenize(text_value: str) -> set[str]:
        return {token for token in re.findall(r"[a-z0-9]+", text_value.lower()) if len(token) > 1}

    def _keyword_overlap_score(self, query_terms: set[str], chunk_text: str) -> float:
        if not query_terms:
            return 0.0
        chunk_terms = self._tokenize(chunk_text)
        if not chunk_terms:
            return 0.0
        return len(query_terms & chunk_terms) / len(query_terms)

    def _metadata_match_score(self, chunk: DocumentChunk, query_text: str, page_number: str) -> float:
        lowered_query = query_text.lower()
        if chunk.section_title and lowered_query in chunk.section_title.lower():
            return 1.0
        if page_number and chunk.page_number is not None and str(chunk.page_number) == page_number:
            return 0.9
        filename = str(chunk.metadata_json.get("filename", "")).lower()
        if lowered_query and lowered_query in filename:
            return 0.7
        return 0.0

    @staticmethod
    def _cosine_similarity(query_vector: list[float], chunk_vector: list[float]) -> float:
        if len(query_vector) != len(chunk_vector) or not query_vector:
            return 0.0
        return max(0.0, sum(left * right for left, right in zip(query_vector, chunk_vector, strict=False)))
