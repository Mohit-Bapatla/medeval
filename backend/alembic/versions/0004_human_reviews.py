"""Add human review records.

Revision ID: 0004_human_reviews
Revises: 0003_qa_rag_eval_experiments
Create Date: 2026-05-24
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0004_human_reviews"
down_revision = "0003_qa_rag_eval_experiments"
branch_labels = None
depends_on = None


def timestamp_column(name: str) -> sa.Column:
    return sa.Column(
        name,
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        nullable=False,
    )


def upgrade() -> None:
    op.create_table(
        "human_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "model_response_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("model_responses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("reviewer_name", sa.String(length=160), nullable=True),
        sa.Column("reviewer_role", sa.String(length=160), nullable=True),
        sa.Column("correctness_label", sa.String(length=80), nullable=True),
        sa.Column("groundedness_label", sa.String(length=80), nullable=True),
        sa.Column("refusal_label", sa.String(length=80), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
    )
    op.create_index("ix_human_reviews_model_response_id", "human_reviews", ["model_response_id"])


def downgrade() -> None:
    op.drop_index("ix_human_reviews_model_response_id", table_name="human_reviews")
    op.drop_table("human_reviews")
