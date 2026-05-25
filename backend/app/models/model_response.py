import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import GUID


class ModelResponse(Base):
    __tablename__ = "model_responses"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    experiment_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("experiments.id", ondelete="SET NULL"), nullable=True, index=True
    )
    qa_example_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("qa_examples.id", ondelete="CASCADE"), nullable=False, index=True
    )
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    answerability: Mapped[str] = mapped_column(String(40), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    cited_chunk_ids_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    retrieved_chunk_ids_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    raw_model_output: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model_provider: Mapped[str] = mapped_column(String(120), nullable=False)
    model_name: Mapped[str] = mapped_column(String(160), nullable=False)
    prompt_template_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("prompt_templates.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    experiment = relationship("Experiment", back_populates="model_responses")
    qa_example = relationship("QAExample", back_populates="model_responses")
    prompt_template = relationship("PromptTemplate")
    retrieved_chunks = relationship(
        "ResponseRetrievedChunk",
        back_populates="model_response",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    evaluation_results = relationship(
        "EvaluationResult",
        back_populates="model_response",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ResponseRetrievedChunk(Base):
    __tablename__ = "response_retrieved_chunks"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    model_response_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("model_responses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("document_chunks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    was_cited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    model_response = relationship("ModelResponse", back_populates="retrieved_chunks")
    chunk = relationship("DocumentChunk")
