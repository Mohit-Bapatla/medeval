import uuid
from typing import Any

from pydantic import BaseModel, Field, field_validator


class RetrievalFilters(BaseModel):
    document_id: uuid.UUID | None = None
    document_type: str | None = Field(default=None, max_length=80)
    source_type: str | None = Field(default=None, max_length=80)


class RetrievalSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)
    document_id: uuid.UUID | None = None
    filters: RetrievalFilters | None = None

    @field_validator("query")
    @classmethod
    def strip_query(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Query cannot be blank")
        return value


class RetrievalResultRead(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_title: str
    chunk_index: int
    chunk_text: str
    similarity_score: float
    metadata: dict[str, Any]


class RetrievalSearchResponse(BaseModel):
    query: str
    top_k: int
    embedding_model: str
    results: list[RetrievalResultRead]
