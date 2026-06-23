from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DocumentBase(BaseModel):
    filename: str
    document_type: str | None = None
    source_path: str | None = None
    status: str = "uploaded"


class DocumentCreate(DocumentBase):
    pass


class DocumentRead(DocumentBase):
    id: int
    created_at: datetime
    processed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class DocumentUploadResponse(DocumentRead):
    message: str


class DocumentProcessResponse(BaseModel):
    document_id: int
    status: str
    chunks_created: int
    message: str


class DocumentChunkBase(BaseModel):
    document_id: int
    chunk_index: int
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentChunkRead(DocumentChunkBase):
    id: int
    created_at: datetime
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="chunk_metadata",
        serialization_alias="metadata",
    )

    model_config = ConfigDict(from_attributes=True)
