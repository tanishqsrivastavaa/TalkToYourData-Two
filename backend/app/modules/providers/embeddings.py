from __future__ import annotations

import math
from hashlib import blake2b
from typing import Protocol

from backend.app.core.config import Settings, get_settings


class EmbeddingProvider(Protocol):
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...


class HashEmbeddingProvider:
    def __init__(self, dimension: int) -> None:
        self.dimension = dimension

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_text(text) for text in texts]

    def _embed_text(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        tokens = [token for token in text.lower().split() if token]
        if not tokens:
            return vector

        for token in tokens:
            digest = blake2b(token.encode("utf-8", errors="ignore"), digest_size=16).digest()
            slot = int.from_bytes(digest[:8], byteorder="big") % self.dimension
            sign = 1.0 if digest[8] % 2 == 0 else -1.0
            weight = 1.0 + (digest[9] / 255.0)
            vector[slot] += sign * weight

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]


class NoopEmbeddingProvider:
    def __init__(self, dimension: int) -> None:
        self.dimension = dimension

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * self.dimension for _ in texts]


def get_embedding_provider(settings: Settings | None = None) -> EmbeddingProvider:
    settings = settings or get_settings()
    if settings.embedding_provider == "noop":
        return NoopEmbeddingProvider(settings.embedding_dimension)
    return HashEmbeddingProvider(settings.embedding_dimension)
