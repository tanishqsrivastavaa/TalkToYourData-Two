"""add pgvector and full text search support

Revision ID: 20260412_0002
Revises: 20260412_0001
Create Date: 2026-04-12 00:30:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260412_0002"
down_revision: str | None = "20260412_0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

EMBEDDING_DIMENSION = 256


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        f"""
        ALTER TABLE document_chunks
        ADD COLUMN embedding_vector vector({EMBEDDING_DIMENSION})
        GENERATED ALWAYS AS (
            CASE
                WHEN json_array_length(embedding) = {EMBEDDING_DIMENSION}
                THEN (embedding::text)::vector
                ELSE NULL
            END
        ) STORED
        """
    )
    op.execute(
        """
        ALTER TABLE document_chunks
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            to_tsvector(
                'english',
                coalesce(section_title, '') || ' ' || coalesce(text, '')
            )
        ) STORED
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_document_chunks_search_vector
        ON document_chunks
        USING GIN (search_vector)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding_vector_hnsw
        ON document_chunks
        USING hnsw (embedding_vector vector_cosine_ops)
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding_vector_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_search_vector")
    op.execute("ALTER TABLE document_chunks DROP COLUMN IF EXISTS search_vector")
    op.execute("ALTER TABLE document_chunks DROP COLUMN IF EXISTS embedding_vector")
