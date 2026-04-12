from backend.app.modules.providers.embeddings import get_embedding_provider
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.modules.providers.generation import GenerationProvider, NoopGenerationProvider
from backend.app.modules.queries.planner import QueryPlanner
from backend.app.modules.queries.schemas import Citation, QueryRequest, QueryResponse
from backend.app.modules.retrieval.service import HybridRetrievalService


class QueryService:
    def __init__(
        self,
        session: AsyncSession,
        planner: QueryPlanner | None = None,
        generator: GenerationProvider | None = None,
    ) -> None:
        self.session = session
        self.planner = planner or QueryPlanner()
        self.generator = generator or NoopGenerationProvider()
        self.retrieval_service = HybridRetrievalService(session, embedding_provider=get_embedding_provider())

    async def answer(self, payload: QueryRequest) -> QueryResponse:
        plan = await self.planner.plan(payload.question, payload.document_ids)
        candidates = await self.retrieval_service.retrieve(plan)
        context = "\n\n".join(candidate.text for candidate in candidates)
        answer = await self.generator.generate_answer(payload.question, context)
        citations = [
            Citation(
                chunk_id=candidate.chunk_id,
                document_id=candidate.document_id,
                section=candidate.section_title,
                page=candidate.page_number,
            )
            for candidate in candidates
        ]
        return QueryResponse(answer=answer, sources=citations, planner=plan)
