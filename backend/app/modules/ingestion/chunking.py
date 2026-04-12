from dataclasses import dataclass


@dataclass(slots=True)
class TextChunk:
    chunk_index: int
    text: str
    token_count: int
    metadata: dict[str, str | int]


class SemanticChunker:
    def __init__(self, chunk_size: int, chunk_overlap: int) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, text: str, metadata: dict[str, str | int] | None = None) -> list[TextChunk]:
        cleaned = " ".join(text.split())
        if not cleaned:
            return []

        metadata = metadata or {}
        step = max(self.chunk_size - self.chunk_overlap, 1)
        chunks: list[TextChunk] = []
        for chunk_index, start in enumerate(range(0, len(cleaned), step)):
            chunk_text = cleaned[start : start + self.chunk_size]
            if not chunk_text:
                continue
            chunks.append(
                TextChunk(
                    chunk_index=chunk_index,
                    text=chunk_text,
                    token_count=max(len(chunk_text.split()), 1),
                    metadata=metadata,
                )
            )
            if start + self.chunk_size >= len(cleaned):
                break
        return chunks
