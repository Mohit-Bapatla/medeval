import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import GUID


class QAExample(Base):
    __tablename__ = "qa_examples"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    gold_answer: Mapped[str] = mapped_column(Text, nullable=False)
    answerability: Mapped[str] = mapped_column(String(40), nullable=False)
    category: Mapped[str] = mapped_column(String(120), nullable=False, default="general")
    difficulty: Mapped[str] = mapped_column(String(40), nullable=False, default="easy")
    risk_level: Mapped[str] = mapped_column(String(40), nullable=False, default="low")
    expected_behavior: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_human: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    dataset = relationship("Dataset", back_populates="qa_examples")
    document = relationship("Document")
    evidence_links = relationship(
        "EvidenceLink",
        back_populates="qa_example",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    model_responses = relationship(
        "ModelResponse",
        back_populates="qa_example",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
