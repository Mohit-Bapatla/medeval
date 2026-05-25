import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class EvaluationResultRead(BaseModel):
    id: uuid.UUID
    model_response_id: uuid.UUID
    correctness_score: float | None
    groundedness_score: float | None
    citation_precision: float | None
    citation_recall: float | None
    retrieval_precision: float | None
    retrieval_recall: float | None
    refusal_score: float | None
    hallucination_flag: bool
    overall_score: float | None
    failure_type: str | None
    evaluator_name: str
    evaluator_version: str
    judge_explanation: str | None
    metadata: dict[str, Any]
    created_at: datetime
