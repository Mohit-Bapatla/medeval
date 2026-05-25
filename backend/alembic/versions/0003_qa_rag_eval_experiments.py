"""Create QA, RAG, evaluation, and experiment tables.

Revision ID: 0003_qa_rag_eval_experiments
Revises: 0002_core_documents_retrieval
Create Date: 2026-05-24
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0003_qa_rag_eval_experiments"
down_revision = "0002_core_documents_retrieval"
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
        "datasets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.String(length=80), nullable=False),
        sa.Column("source", sa.String(length=120), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
    )
    op.create_index("ix_datasets_name", "datasets", ["name"])

    op.create_table(
        "prompt_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("version", sa.String(length=80), nullable=False),
        sa.Column("template_text", sa.Text(), nullable=False),
        sa.Column("template_type", sa.String(length=80), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
    )
    op.create_index("ix_prompt_templates_name", "prompt_templates", ["name"])
    op.create_index("ix_prompt_templates_template_type", "prompt_templates", ["template_type"])

    op.create_table(
        "qa_examples",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "dataset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("datasets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("gold_answer", sa.Text(), nullable=False),
        sa.Column("answerability", sa.String(length=40), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=False),
        sa.Column("difficulty", sa.String(length=40), nullable=False),
        sa.Column("risk_level", sa.String(length=40), nullable=False),
        sa.Column("expected_behavior", sa.Text(), nullable=True),
        sa.Column("reviewed_by_human", sa.Boolean(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
    )
    op.create_index("ix_qa_examples_dataset_id", "qa_examples", ["dataset_id"])
    op.create_index("ix_qa_examples_document_id", "qa_examples", ["document_id"])

    op.create_table(
        "evidence_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "qa_example_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("qa_examples.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "chunk_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("document_chunks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("evidence_role", sa.String(length=40), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        timestamp_column("created_at"),
    )
    op.create_index("ix_evidence_links_qa_example_id", "evidence_links", ["qa_example_id"])
    op.create_index("ix_evidence_links_chunk_id", "evidence_links", ["chunk_id"])

    op.create_table(
        "experiments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "dataset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("datasets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("model_provider", sa.String(length=120), nullable=False),
        sa.Column("model_name", sa.String(length=160), nullable=False),
        sa.Column("embedding_model", sa.String(length=160), nullable=False),
        sa.Column(
            "prompt_template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("prompt_templates.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("retrieval_strategy", sa.String(length=120), nullable=False),
        sa.Column("top_k", sa.Integer(), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
    )
    op.create_index("ix_experiments_name", "experiments", ["name"])
    op.create_index("ix_experiments_dataset_id", "experiments", ["dataset_id"])

    op.create_table(
        "model_responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "experiment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("experiments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "qa_example_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("qa_examples.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("answerability", sa.String(length=40), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("cited_chunk_ids_json", sa.JSON(), nullable=False),
        sa.Column("retrieved_chunk_ids_json", sa.JSON(), nullable=False),
        sa.Column("raw_model_output", sa.JSON(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("estimated_cost", sa.Float(), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("model_provider", sa.String(length=120), nullable=False),
        sa.Column("model_name", sa.String(length=160), nullable=False),
        sa.Column(
            "prompt_template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("prompt_templates.id", ondelete="SET NULL"),
            nullable=True,
        ),
        timestamp_column("created_at"),
    )
    op.create_index("ix_model_responses_experiment_id", "model_responses", ["experiment_id"])
    op.create_index("ix_model_responses_qa_example_id", "model_responses", ["qa_example_id"])

    op.create_table(
        "response_retrieved_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "model_response_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("model_responses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "chunk_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("document_chunks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("similarity_score", sa.Float(), nullable=False),
        sa.Column("was_cited", sa.Boolean(), nullable=False),
        timestamp_column("created_at"),
    )
    op.create_index(
        "ix_response_retrieved_chunks_model_response_id",
        "response_retrieved_chunks",
        ["model_response_id"],
    )
    op.create_index(
        "ix_response_retrieved_chunks_chunk_id",
        "response_retrieved_chunks",
        ["chunk_id"],
    )

    op.create_table(
        "evaluation_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "model_response_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("model_responses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("correctness_score", sa.Float(), nullable=True),
        sa.Column("groundedness_score", sa.Float(), nullable=True),
        sa.Column("citation_precision", sa.Float(), nullable=True),
        sa.Column("citation_recall", sa.Float(), nullable=True),
        sa.Column("retrieval_precision", sa.Float(), nullable=True),
        sa.Column("retrieval_recall", sa.Float(), nullable=True),
        sa.Column("refusal_score", sa.Float(), nullable=True),
        sa.Column("hallucination_flag", sa.Boolean(), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("failure_type", sa.String(length=120), nullable=True),
        sa.Column("evaluator_name", sa.String(length=160), nullable=False),
        sa.Column("evaluator_version", sa.String(length=80), nullable=False),
        sa.Column("judge_explanation", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        timestamp_column("created_at"),
    )
    op.create_index(
        "ix_evaluation_results_model_response_id",
        "evaluation_results",
        ["model_response_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_evaluation_results_model_response_id", table_name="evaluation_results")
    op.drop_table("evaluation_results")
    op.drop_index("ix_response_retrieved_chunks_chunk_id", table_name="response_retrieved_chunks")
    op.drop_index(
        "ix_response_retrieved_chunks_model_response_id",
        table_name="response_retrieved_chunks",
    )
    op.drop_table("response_retrieved_chunks")
    op.drop_index("ix_model_responses_qa_example_id", table_name="model_responses")
    op.drop_index("ix_model_responses_experiment_id", table_name="model_responses")
    op.drop_table("model_responses")
    op.drop_index("ix_experiments_dataset_id", table_name="experiments")
    op.drop_index("ix_experiments_name", table_name="experiments")
    op.drop_table("experiments")
    op.drop_index("ix_evidence_links_chunk_id", table_name="evidence_links")
    op.drop_index("ix_evidence_links_qa_example_id", table_name="evidence_links")
    op.drop_table("evidence_links")
    op.drop_index("ix_qa_examples_document_id", table_name="qa_examples")
    op.drop_index("ix_qa_examples_dataset_id", table_name="qa_examples")
    op.drop_table("qa_examples")
    op.drop_index("ix_prompt_templates_template_type", table_name="prompt_templates")
    op.drop_index("ix_prompt_templates_name", table_name="prompt_templates")
    op.drop_table("prompt_templates")
    op.drop_index("ix_datasets_name", table_name="datasets")
    op.drop_table("datasets")
