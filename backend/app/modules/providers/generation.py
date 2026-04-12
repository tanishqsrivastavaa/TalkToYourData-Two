from __future__ import annotations

from typing import Protocol


class GenerationProvider(Protocol):
    async def generate_answer(self, question: str, context: str) -> str:
        ...


class NoopGenerationProvider:
    async def generate_answer(self, question: str, context: str) -> str:
        if not context.strip():
            return "No grounded answer could be generated because no supporting context was retrieved."
        return f"Grounded answer draft for: {question}\n\n{context[:1000]}"
