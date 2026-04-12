"""initial schema

Revision ID: 20260412_0001
Revises:
Create Date: 2026-04-12 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260412_0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.Enum("pdf", "txt", "markdown", "webpage", name="sourcetype"), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "processing", "indexed", "failed", name="documentstatus"),
            nullable=False,
        ),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_documents_filename"), "documents", ["filename"], unique=False)
    op.create_index(op.f("ix_documents_source_type"), "documents", ["source_type"], unique=False)
    op.create_index(op.f("ix_documents_status"), "documents", ["status"], unique=False)

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("section_title", sa.String(length=512), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("embedding", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_document_chunks_chunk_index"), "document_chunks", ["chunk_index"], unique=False)
    op.create_index(op.f("ix_document_chunks_document_id"), "document_chunks", ["document_id"], unique=False)
    op.create_index(
        "ix_document_chunks_document_chunk_index",
        "document_chunks",
        ["document_id", "chunk_index"],
        unique=False,
    )
    op.create_index(op.f("ix_document_chunks_page_number"), "document_chunks", ["page_number"], unique=False)
    op.create_index(op.f("ix_document_chunks_section_title"), "document_chunks", ["section_title"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_document_chunks_section_title"), table_name="document_chunks")
    op.drop_index(op.f("ix_document_chunks_page_number"), table_name="document_chunks")
    op.drop_index("ix_document_chunks_document_chunk_index", table_name="document_chunks")
    op.drop_index(op.f("ix_document_chunks_document_id"), table_name="document_chunks")
    op.drop_index(op.f("ix_document_chunks_chunk_index"), table_name="document_chunks")
    op.drop_table("document_chunks")

    op.drop_index(op.f("ix_documents_status"), table_name="documents")
    op.drop_index(op.f("ix_documents_source_type"), table_name="documents")
    op.drop_index(op.f("ix_documents_filename"), table_name="documents")
    op.drop_table("documents")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP TYPE IF EXISTS documentstatus")
        op.execute("DROP TYPE IF EXISTS sourcetype")
