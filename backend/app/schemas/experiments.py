import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

ExperimentStatus = Literal["draft", "running", "completed", "failed"]


class ExperimentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    dataset_id: uuid.UUID
    description: str | None = None
    model_provider: str = "deterministic_local"
    model_name: str = "deterministic-extractive-answer-v1"
    embedding_model: str = "deterministic-hash-embedding-384"
    prompt_template_id: uuid.UUID | None = None
    retrieval_strategy: str = "vector_similarity"
    top_k: int = Field(default=5, ge=1, le=50)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExperimentRead(ExperimentCreate):
    id: uuid.UUID
    status: ExperimentStatus
    created_at: datetime
    updated_at: datetime


class ExperimentRunResponse(BaseModel):
    experiment: ExperimentRead
    examples_run: int
    model_responses_created: int
    evaluations_created: int


class ExperimentAggregateResults(BaseModel):
    experiment_id: uuid.UUID
    status: str
    example_count: int
    avg_correctness: float | None
    avg_groundedness: float | None
    avg_citation_precision: float | None
    avg_citation_recall: float | None
    avg_retrieval_precision: float | None
    avg_retrieval_recall: float | None
    refusal_accuracy: float | None
    hallucination_rate: float | None
    failure_type_counts: dict[str, int]
    avg_latency_ms: float | None
    total_estimated_cost: float | None
