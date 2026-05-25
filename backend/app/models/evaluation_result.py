import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import GUID


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    model_response_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("model_responses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    correctness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    groundedness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    citation_precision: Mapped[float | None] = mapped_column(Float, nullable=True)
    citation_recall: Mapped[float | None] = mapped_column(Float, nullable=True)
    retrieval_precision: Mapped[float | None] = mapped_column(Float, nullable=True)
    retrieval_recall: Mapped[float | None] = mapped_column(Float, nullable=True)
    refusal_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    hallucination_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    failure_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    evaluator_name: Mapped[str] = mapped_column(String(160), nullable=False)
    evaluator_version: Mapped[str] = mapped_column(String(80), nullable=False)
    judge_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    model_response = relationship("ModelResponse", back_populates="evaluation_results")
