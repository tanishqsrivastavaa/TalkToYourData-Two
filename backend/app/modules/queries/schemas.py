from uuid import UUID

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=3)
    document_ids: list[UUID] = Field(default_factory=list)


class QueryPlan(BaseModel):
    intent: str
    sub_queries: list[str]
    retrieval_mode: str = "hybrid"
    document_ids: list[UUID] = Field(default_factory=list)


class Citation(BaseModel):
    chunk_id: UUID
    document_id: UUID
    section: str | None = None
    page: int | None = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[Citation]
    planner: QueryPlan
