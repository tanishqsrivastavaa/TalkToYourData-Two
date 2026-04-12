from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.core.logging import configure_logging
from backend.app.db.init_db import initialize_database


@asynccontextmanager
async def app_lifespan(_: FastAPI):
    configure_logging()
    await initialize_database()
    yield
