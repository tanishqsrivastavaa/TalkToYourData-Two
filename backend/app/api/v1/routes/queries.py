from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_session
from backend.app.modules.queries.schemas import QueryRequest, QueryResponse
from backend.app.modules.queries.service import QueryService

router = APIRouter(prefix="/queries", tags=["queries"])


@router.post("", response_model=QueryResponse)
async def query_documents(
    payload: QueryRequest,
    session: AsyncSession = Depends(get_session),
) -> QueryResponse:
    service = QueryService(session)
    return await service.answer(payload)
