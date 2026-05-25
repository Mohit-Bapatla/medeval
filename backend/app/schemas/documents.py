import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DocumentBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    source_url: str | None = Field(default=None, max_length=2048)
    source_type: str = Field(default="unknown", max_length=80)
    organization_name: str | None = Field(default=None, max_length=255)
    document_type: str = Field(default="unknown", max_length=80)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("title", "source_type", "document_type")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Value cannot be blank")
        return value


class DocumentCreate(DocumentBase):
    raw_text: str = Field(min_length=1)

    @field_validator("raw_text")
    @classmethod
    def strip_raw_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Document text cannot be blank")
        return value


class DocumentRead(DocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    raw_text: str
    cleaned_text: str
    created_at: datetime
    updated_at: datetime


class DocumentListItem(DocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class DocumentChunkRequest(BaseModel):
    chunk_size_chars: int = Field(default=1800, ge=200, le=10000)
    chunk_overlap_chars: int = Field(default=250, ge=0, le=5000)
    min_chunk_chars: int = Field(default=200, ge=1, le=5000)
    replace_existing: bool = True

    @field_validator("chunk_overlap_chars")
    @classmethod
    def overlap_must_be_smaller_than_size(cls, value: int, info: Any) -> int:
        chunk_size = info.data.get("chunk_size_chars")
        if chunk_size is not None and value >= chunk_size:
            raise ValueError("chunk_overlap_chars must be smaller than chunk_size_chars")
        return value


class DocumentEmbedRequest(BaseModel):
    force: bool = False


class BulkEmbedRequest(BaseModel):
    force: bool = False
    limit: int | None = Field(default=None, ge=1, le=1000)


class EmbedResponse(BaseModel):
    embedded_chunks: int
    embedding_model: str
    embedding_dimension: int
