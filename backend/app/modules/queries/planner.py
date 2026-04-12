from pydantic import BaseModel
from pydantic_ai import Agent

from backend.app.modules.queries.schemas import QueryPlan


class QueryPlannerOutput(BaseModel):
    intent: str
    sub_queries: list[str]
    retrieval_mode: str = "hybrid"


PLANNER_INSTRUCTIONS = """
You are a query planning component for a reasoning-first hybrid RAG backend.
Classify the user question, decompose it into retrieval-oriented sub-queries,
and choose a retrieval mode. Use one of these intents:
explain, summarize, compare, definition, multi_hop.
Prefer concise sub-queries that can drive retrieval.
""".strip()


class QueryPlanner:
    def __init__(self) -> None:
        self.agent = Agent(
            "test",
            output_type=QueryPlannerOutput,
            system_prompt=PLANNER_INSTRUCTIONS,
        )

    async def plan(self, question: str, document_ids: list) -> QueryPlan:
        lower_question = question.lower()
        if "compare" in lower_question:
            intent = "compare"
        elif "summary" in lower_question or "summarize" in lower_question:
            intent = "summarize"
        elif "define" in lower_question or "definition" in lower_question:
            intent = "definition"
        elif " and " in lower_question or "before" in lower_question:
            intent = "multi_hop"
        else:
            intent = "explain"

        sub_queries = [part.strip(" ?") for part in question.split(" and ") if part.strip()]
        return QueryPlan(
            intent=intent,
            sub_queries=sub_queries or [question],
            retrieval_mode="hybrid",
            document_ids=document_ids,
        )
