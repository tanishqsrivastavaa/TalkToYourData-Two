# Talk to Your Data Two

Reasoning-first RAG backend built with FastAPI, SQLModel, and PostgreSQL-first retrieval primitives.

## What Works

- document upload for `.txt`, `.md`, and basic `.pdf` fallback parsing
- chunking and embedding generation during ingestion
- document lookup by ID
- query planning plus grounded answer generation
- PostgreSQL hybrid retrieval when `pgvector`/FTS columns exist
- SQLite/local fallback retrieval for development and tests

## Run It

```bash
uv run fastapi dev backend/app/main.py
```

The API mounts under `/api/v1`.

## Main Endpoints

- `POST /api/v1/documents/upload`
- `GET /api/v1/documents/{document_id}`
- `POST /api/v1/queries`
- `GET /api/v1/health`

## Notes

- On startup, the app bootstraps the schema for local development.
- For PostgreSQL production use, keep Alembic migrations as the source of truth for advanced database features such as generated `pgvector` and full-text-search columns.
