import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

CorrectnessLabel = Literal["correct", "partially_correct", "incorrect", "unsure"]
GroundednessLabel = Literal["grounded", "partially_grounded", "unsupported", "unsure"]
RefusalLabel = Literal[
    "correct_refusal",
    "failed_refusal",
    "over_refusal",
    "not_applicable",
]


class HumanReviewCreate(BaseModel):
    reviewer_name: str | None = Field(default=None, max_length=160)
    reviewer_role: str | None = Field(default=None, max_length=160)
    correctness_label: CorrectnessLabel | None = None
    groundedness_label: GroundednessLabel | None = None
    refusal_label: RefusalLabel | None = None
    notes: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class HumanReviewRead(HumanReviewCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    model_response_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
