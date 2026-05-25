import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

DatasetSource = Literal["synthetic_demo", "imported_jsonl", "imported_csv", "manual"]


class DatasetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    version: str = Field(default="0.1.0-dev", max_length=80)
    source: DatasetSource = "synthetic_demo"
    metadata: dict[str, Any] = Field(default_factory=dict)


class DatasetRead(DatasetCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class DatasetImportResponse(BaseModel):
    dataset_id: uuid.UUID
    imported_examples: int
    evidence_links_created: int
    skipped_evidence_links: int
