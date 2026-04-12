from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from backend.app.db.models import DocumentStatus, SourceType


class DocumentCreate(BaseModel):
    filename: str
    content_type: str
    source_type: SourceType
    metadata: dict[str, str] | None = None


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    content_type: str
    source_type: SourceType
    status: DocumentStatus
    metadata_json: dict
    created_at: datetime
    updated_at: datetime


class UploadResponse(BaseModel):
    status: str
    document_id: UUID
    message: str
