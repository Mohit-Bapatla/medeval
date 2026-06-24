import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

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


ReviewerType = Literal["self", "student", "domain_reviewer", "clinician", "unknown"]
ReviewStatus = Literal["pending", "completed", "skipped"]
SeverityOverride = Literal["low", "medium", "high", "critical"]
AdjudicationStatus = Literal["none", "needs_second_review", "adjudicated"]


class MedEvalV1ReviewUpsert(BaseModel):
    reviewer_label: str = Field(min_length=1, max_length=160)
    reviewer_type: ReviewerType = "unknown"
    review_status: ReviewStatus = "completed"
    answer_correctness: int | None = None
    groundedness: int | None = None
    citation_quality: int | None = None
    refusal_safety: int | None = None
    should_refuse: bool | None = None
    did_refuse: bool | None = None
    selected_failure_categories: list[str] = Field(default_factory=list)
    severity_override: SeverityOverride | None = None
    review_notes: str | None = None
    confidence: int | None = None
    reviewer_time_seconds: int | None = None
    adjudication_status: AdjudicationStatus = "none"
    sample: bool = False
    sample_notes: str | None = None

    @field_validator(
        "answer_correctness",
        "groundedness",
        "citation_quality",
        "refusal_safety",
        "confidence",
    )
    @classmethod
    def score_must_be_1_to_5(cls, value: int | None) -> int | None:
        if value is None:
            return value
        if value < 1 or value > 5:
            raise ValueError("score must be between 1 and 5")
        return value


class ReviewQueueRead(BaseModel):
    metadata: dict[str, Any]
    experiment: dict[str, Any]
    items: list[dict[str, Any]]


class ReviewSummaryRead(BaseModel):
    metadata: dict[str, Any]
    experiment: dict[str, Any]
    review_count: int
    completed_review_count: int
    rubric_averages: dict[str, float]
    calibration: dict[str, Any]
    reviewer_failure_category_counts: dict[str, int]
    reviewer_override_count: int
    rows: list[dict[str, Any]]
    limitations: list[str]
    markdown: str


class HumanReviewRead(HumanReviewCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    model_response_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
