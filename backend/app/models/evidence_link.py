import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import GUID


class EvidenceLink(Base):
    __tablename__ = "evidence_links"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    qa_example_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("qa_examples.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("document_chunks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence_role: Mapped[str] = mapped_column(String(40), nullable=False, default="required")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    qa_example = relationship("QAExample", back_populates="evidence_links")
    chunk = relationship("DocumentChunk")
