import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ChunkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    chunk_text: str
    token_count: int
    char_start: int | None
    char_end: int | None
    page_number: int | None
    section_title: str | None
    embedding_model: str | None
    metadata: dict[str, Any]
    created_at: datetime


class ChunkingResponse(BaseModel):
    document_id: uuid.UUID
    chunks_created: int
    chunks: list[ChunkRead]
