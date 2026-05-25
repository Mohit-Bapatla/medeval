import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Answerability = Literal["answerable", "unanswerable", "ambiguous"]
Difficulty = Literal["easy", "medium", "hard"]
RiskLevel = Literal["low", "medium", "high"]
EvidenceRole = Literal["required", "acceptable", "supporting"]


class QAExampleCreate(BaseModel):
    document_id: uuid.UUID | None = None
    question: str = Field(min_length=1)
    gold_answer: str = Field(min_length=1)
    answerability: Answerability = "answerable"
    category: str = Field(default="general", max_length=120)
    difficulty: Difficulty = "easy"
    risk_level: RiskLevel = "low"
    expected_behavior: str | None = None
    reviewed_by_human: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("question", "gold_answer")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Value cannot be blank")
        return value


class QAExampleRead(QAExampleCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dataset_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class EvidenceLinkCreate(BaseModel):
    chunk_id: uuid.UUID
    evidence_role: EvidenceRole = "required"
    notes: str | None = None


class EvidenceReference(BaseModel):
    chunk_id: uuid.UUID | None = None
    document_title: str | None = None
    document_file: str | None = None
    chunk_index: int | None = None
    evidence_role: EvidenceRole = "required"
    notes: str | None = None


class EvidenceLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    qa_example_id: uuid.UUID
    chunk_id: uuid.UUID
    evidence_role: str
    notes: str | None
    created_at: datetime
