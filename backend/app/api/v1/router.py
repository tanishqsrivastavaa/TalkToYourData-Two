from fastapi import APIRouter

from backend.app.api.v1.routes.documents import router as documents_router
from backend.app.api.v1.routes.health import router as health_router
from backend.app.api.v1.routes.queries import router as queries_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(documents_router)
api_router.include_router(queries_router)
