from backend.app.core.config import get_settings
from backend.app.modules.retrieval.schemas import RetrievalCandidate


class FusionReranker:
    def __init__(self) -> None:
        settings = get_settings()
        self.vector_weight = settings.retrieval_vector_weight
        self.keyword_weight = settings.retrieval_keyword_weight
        self.metadata_weight = settings.retrieval_metadata_weight

    def score(self, candidate: RetrievalCandidate) -> float:
        return (
            candidate.vector_score * self.vector_weight
            + candidate.keyword_score * self.keyword_weight
            + candidate.metadata_score * self.metadata_weight
        )

    def rank(self, candidates: list[RetrievalCandidate]) -> list[RetrievalCandidate]:
        return sorted(candidates, key=self.score, reverse=True)
