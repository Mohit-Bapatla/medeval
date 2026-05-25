import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.schemas.evaluations import EvaluationResultRead
from app.schemas.experiments import ExperimentAggregateResults, ExperimentRead
from app.schemas.human_reviews import HumanReviewRead
from app.schemas.qa_examples import QAExampleRead
from app.schemas.rag import ModelResponseRead


class TraceChunkRead(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_title: str
    chunk_index: int
    chunk_text: str
    rank: int
    similarity_score: float
    was_cited: bool


class PromptTemplateSummary(BaseModel):
    id: uuid.UUID
    name: str
    version: str
    template_type: str


class ResponseTraceRead(BaseModel):
    model_response: ModelResponseRead
    qa_example: QAExampleRead
    experiment: ExperimentRead | None
    evaluation: EvaluationResultRead | None
    retrieved_chunks: list[TraceChunkRead]
    cited_chunks: list[TraceChunkRead]
    prompt_template: PromptTemplateSummary | None
    human_reviews: list[HumanReviewRead] = []


class ExperimentResponseRow(BaseModel):
    response_id: uuid.UUID
    qa_example_id: uuid.UUID
    question: str
    expected_answerability: str
    model_answerability: str
    answer_text: str
    correctness_score: float | None
    groundedness_score: float | None
    hallucination_flag: bool | None
    failure_type: str | None
    primary_failure_type: str | None = None
    secondary_failure_types: list[str] = []
    failure_reason: str | None = None
    retrieval_failure: bool | None = None
    generation_failure: bool | None = None
    claim_count: int | None = None
    claim_support_rate: float | None = None
    unsupported_claim_rate: float | None = None
    created_at: datetime


class ExperimentFailureRow(ExperimentResponseRow):
    failure_reason: str


class ExperimentReport(BaseModel):
    experiment: ExperimentRead
    results: ExperimentAggregateResults
    failure_examples: list[ExperimentFailureRow]
    markdown: str
    generated_at: datetime
    disclaimer: str
    metadata: dict[str, Any]
