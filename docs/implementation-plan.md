# Talk to Your Data: Implementation Plan

## System Goal

Build a production-oriented FastAPI backend for a reasoning-first hybrid RAG system that ingests academic documents, stores searchable chunks in PostgreSQL with `pgvector`, plans retrieval with a typed PydanticAI query planner, and returns grounded cited answers.

## Architectural Principles

- Reason first, retrieve second.
- Keep AI outputs type-safe and validated.
- Separate orchestration from provider implementations.
- Keep vector, metadata, and keyword search unified in PostgreSQL.
- Design now for future async ingestion workers and chat sessions.

## Request Flows

### Upload flow

1. Client uploads a supported file.
2. API stores a document record with ingestion status.
3. Parsing extracts structured text segments and metadata.
4. Chunking creates overlapping semantic chunks.
5. Embedding provider generates vectors for chunks.
6. Chunks are stored with metadata, keyword search data, and embeddings.
7. API returns document identifier and indexing status.

### Query flow

1. Client submits a natural-language question and optional document filters.
2. Query planner classifies intent and decomposes sub-queries.
3. Retrieval orchestrator runs semantic, keyword, and metadata retrieval.
4. Fusion service deduplicates and re-ranks candidate chunks.
5. Response generator answers strictly from fused evidence.
6. API returns answer plus structured citations.

## Module Layout

### `backend/app/core`

- `config.py`: environment-driven settings and provider selection
- `logging.py`: centralized logging setup
- `lifespan.py`: startup/shutdown hooks

### `backend/app/db`

- `models.py`: `Document`, `DocumentChunk`, future `ChatSession`
- `session.py`: async SQLAlchemy engine and session factory
- `init_db.py`: extension creation and metadata bootstrap

### `backend/app/modules/documents`

- `schemas.py`: upload/document DTOs
- `service.py`: document creation and retrieval

### `backend/app/modules/ingestion`

- `parsers.py`: file-type parsing interfaces and parser registry
- `chunking.py`: semantic chunking configuration and logic
- `service.py`: ingestion orchestration

### `backend/app/modules/providers`

- `embeddings.py`: embedding provider protocol and implementations
- `generation.py`: answer-generation provider protocol

### `backend/app/modules/queries`

- `planner.py`: PydanticAI query planner
- `schemas.py`: query/request/response DTOs
- `service.py`: query orchestration entrypoint

### `backend/app/modules/retrieval`

- `schemas.py`: retrieval candidate models
- `service.py`: hybrid retrieval orchestration
- `rerank.py`: fusion and scoring

### `backend/app/api/v1`

- `router.py`: API v1 router composition
- `routes/documents.py`: upload and document inspection endpoints
- `routes/queries.py`: query endpoint
- `routes/health.py`: readiness checks

## Data Model

### `documents`

- `id`
- `filename`
- `content_type`
- `source_type`
- `status`
- `metadata_json`
- `created_at`
- `updated_at`

### `document_chunks`

- `id`
- `document_id`
- `chunk_index`
- `text`
- `section_title`
- `page_number`
- `token_count`
- `metadata_json`
- `embedding`

## Implementation Phases

1. Foundation
2. Ingestion domain
3. Query domain
4. Provider integration
5. Verification

## Immediate Deliverables In This Iteration

- production-oriented project skeleton
- typed settings and database bootstrap
- document and chunk models
- upload/query API contracts
- ingestion/query orchestration interfaces
- baseline tests proving the app boots and routes are wired
