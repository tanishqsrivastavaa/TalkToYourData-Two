<div align="center">

# 📊 TalkToYourData-Two

**A reasoning-first RAG backend — ask your documents questions, get grounded answers.**

Second generation of TalkToYourData: text-only, retrieval-first, built on PostgreSQL-native search primitives.

![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/DB-PostgreSQL%20%2B%20pgvector-4169E1?logo=postgresql&logoColor=white)
![SQLModel](https://img.shields.io/badge/ORM-SQLModel-red)

</div>

---

## 📖 About

TalkToYourData-Two is a backend for conversational document Q&A. Upload `.txt`, `.md`, or PDF files; the service chunks and embeds them, then answers queries with **grounded, retrieval-backed responses** instead of free-form guesses.

The design principle: *reasoning-first* — query planning happens before answer generation, and answers are grounded in retrieved context.

## ✨ What Works

- 📄 **Document ingestion** — upload `.txt`, `.md`, with basic `.pdf` fallback parsing
- ✂️ **Chunking + embeddings** — generated automatically during ingestion
- 🔍 **Hybrid retrieval** — PostgreSQL `pgvector` semantic search + full-text search (FTS) when available
- 💻 **Local dev fallback** — SQLite-based retrieval for development and tests
- 🧭 **Query planning** — plans the retrieval strategy before generating an answer
- ✅ **Grounded generation** — answers tied to retrieved document context

## 🔌 API

The API mounts under `/api/v1`:

| Method | Route | Description |
|---|---|---|
| `POST` | `/api/v1/documents/upload` | Upload a document |
| `GET` | `/api/v1/documents/{document_id}` | Look up a document by ID |
| `POST` | `/api/v1/queries` | Ask a question |
| `GET` | `/api/v1/health` | Health check |

## 🚀 Run It

Requires [`uv`](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/tanishqsrivastavaa/TalkToYourData-Two.git
cd TalkToYourData-Two
uv sync
uv run fastapi dev backend/app/main.py
```

On startup the app bootstraps its schema for local development.

> **Production note:** for PostgreSQL deployments, keep Alembic migrations as the source of truth — they manage advanced features like generated `pgvector` and full-text-search columns.

## 🏗️ Architecture

```
backend/app/
├── api/v1/routes/     # documents, queries, health endpoints
├── agents/            # Query planning + grounded answer generation
├── core/              # Config, logging, lifespan
├── db/                # Session, models, init
└── modules/           # Feature modules
alembic/               # Migrations (pgvector + FTS columns)
```

## 🧪 Tests

```bash
uv run pytest tests/
```

---

<div align="center">
<sub>Sibling project: [TalkToYourData](https://github.com/tanishqsrivastavaa/TalkToYourData) — the voice-native variant.</sub>
</div>
