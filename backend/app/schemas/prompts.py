import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

PromptTemplateType = Literal["rag_answer", "judge", "citation_check"]


class PromptTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    version: str = Field(min_length=1, max_length=80)
    template_text: str = Field(min_length=1)
    template_type: PromptTemplateType = "rag_answer"
    metadata: dict[str, Any] = Field(default_factory=dict)


class PromptTemplateRead(PromptTemplateCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
