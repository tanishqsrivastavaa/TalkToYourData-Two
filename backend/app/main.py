from fastapi import FastAPI

from backend.app.api.v1.router import api_router
from backend.app.core.config import get_settings
from backend.app.core.lifespan import app_lifespan

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    lifespan=app_lifespan,
)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": settings.app_name}
