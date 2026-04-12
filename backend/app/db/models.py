from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Index, JSON, Text
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DocumentStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    indexed = "indexed"
    failed = "failed"


class SourceType(str, Enum):
    pdf = "pdf"
    txt = "txt"
    markdown = "markdown"
    webpage = "webpage"


class Document(SQLModel, table=True):
    __tablename__ = "documents"

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    filename: str = Field(index=True, max_length=255)
    content_type: str = Field(max_length=255)
    source_type: SourceType = Field(index=True)
    status: DocumentStatus = Field(default=DocumentStatus.pending, index=True)
    metadata_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class DocumentChunk(SQLModel, table=True):
    __tablename__ = "document_chunks"

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    document_id: UUID = Field(
        sa_column=Column(
            ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
    )
    chunk_index: int = Field(index=True, nullable=False)
    text: str = Field(sa_column=Column(Text, nullable=False))
    section_title: str | None = Field(default=None, max_length=512, index=True)
    page_number: int | None = Field(default=None, index=True)
    token_count: int = Field(default=0, nullable=False)
    metadata_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
    )
    embedding: list[float] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


Index(
    "ix_document_chunks_document_chunk_index",
    DocumentChunk.document_id,
    DocumentChunk.chunk_index,
)
