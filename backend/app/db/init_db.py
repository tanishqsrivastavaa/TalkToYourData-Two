from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlmodel import SQLModel

from backend.app.db import models  # noqa: F401
from backend.app.db.session import engine


async def initialize_database() -> None:
    async with engine.begin() as conn:
        if engine.url.get_backend_name().startswith("postgresql"):
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            except DBAPIError:
                pass
        await conn.run_sync(SQLModel.metadata.create_all)
