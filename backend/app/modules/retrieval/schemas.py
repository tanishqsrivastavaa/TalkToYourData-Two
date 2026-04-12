from uuid import UUID

from pydantic import BaseModel, Field


class RetrievalCandidate(BaseModel):
    chunk_id: UUID
    document_id: UUID
    text: str
    section_title: str | None = None
    page_number: int | None = None
    vector_score: float = 0.0
    keyword_score: float = 0.0
    metadata_score: float = 0.0


class RetrievalPlan(BaseModel):
    retrieval_mode: str = "hybrid"
    filters: dict[str, str | int] = Field(default_factory=dict)
