from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Talk to Your Data API"
    app_env: Literal["development", "test", "production"] = "development"
    app_debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    api_v1_prefix: str = "/api/v1"

    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/dbname",
        alias="DATABASE_URL",
    )
    database_echo: bool = False

    openai_api_key: str | None = None
    google_api_key: str | None = None
    embedding_provider: Literal["openai", "google", "huggingface", "hash", "noop"] = "hash"
    embedding_model: str = "text-embedding-3-small"
    llm_provider: Literal["openai", "google", "huggingface", "noop"] = "noop"
    llm_model: str = "gpt-4o-mini"
    embedding_dimension: int = 256

    chunk_size: int = 700
    chunk_overlap: int = 120
    retrieval_vector_weight: float = 0.5
    retrieval_keyword_weight: float = 0.3
    retrieval_metadata_weight: float = 0.2
    max_retrieved_chunks: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()
