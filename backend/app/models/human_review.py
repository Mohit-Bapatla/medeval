import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import GUID


class HumanReview(Base):
    __tablename__ = "human_reviews"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    model_response_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("model_responses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewer_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    reviewer_role: Mapped[str | None] = mapped_column(String(160), nullable=True)
    correctness_label: Mapped[str | None] = mapped_column(String(80), nullable=True)
    groundedness_label: Mapped[str | None] = mapped_column(String(80), nullable=True)
    refusal_label: Mapped[str | None] = mapped_column(String(80), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
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

    model_response = relationship("ModelResponse", back_populates="human_reviews")
