import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.retrieval import RetrievalFilters, RetrievalResultRead


class RagAnswerRequest(BaseModel):
    qa_example_id: uuid.UUID | None = None
    question: str | None = Field(default=None, min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)
    filters: RetrievalFilters | None = None
    experiment_id: uuid.UUID | None = None
    prompt_template_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def require_qa_or_question(self) -> "RagAnswerRequest":
        if self.qa_example_id is None and not self.question:
            raise ValueError("Either qa_example_id or question is required")
        return self


class ProviderAnswer(BaseModel):
    answer: str
    citations: list[str]
    answerability: Literal["answerable", "unanswerable", "ambiguous"]
    confidence: float = Field(ge=0.0, le=1.0)


class ModelResponseRead(BaseModel):
    id: uuid.UUID
    experiment_id: uuid.UUID | None
    qa_example_id: uuid.UUID
    answer_text: str
    answerability: str
    confidence: float | None
    cited_chunk_ids: list[str]
    retrieved_chunk_ids: list[str]
    raw_model_output: dict[str, Any]
    latency_ms: int | None
    estimated_cost: float | None
    input_tokens: int | None
    output_tokens: int | None
    model_provider: str
    model_name: str
    prompt_template_id: uuid.UUID | None
    created_at: datetime


class ResponseRetrievedChunkRead(BaseModel):
    chunk_id: uuid.UUID
    rank: int
    similarity_score: float
    was_cited: bool


class RagTraceResponse(BaseModel):
    model_response: ModelResponseRead | None
    answer: ProviderAnswer
    retrieved_chunks: list[RetrievalResultRead]
    response_retrieved_chunks: list[ResponseRetrievedChunkRead]
    prompt_text: str
