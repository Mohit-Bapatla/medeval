import uuid
from collections import Counter
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.datasets import serialize_qa_example
from app.api.v1.evaluations import serialize_evaluation_result
from app.api.v1.experiments import serialize_experiment
from app.api.v1.rag import serialize_model_response
from app.db.session import get_db
from app.models.evaluation_result import EvaluationResult
from app.models.experiment import Experiment
from app.models.model_response import ModelResponse, ResponseRetrievedChunk
from app.schemas.reports import (
    ExperimentFailureRow,
    ExperimentReport,
    ExperimentResponseRow,
    PromptTemplateSummary,
    ResponseTraceRead,
    TraceChunkRead,
)
from app.services.experiment_service import experiment_service

router = APIRouter(tags=["reports"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/experiments/{experiment_id}/responses", response_model=list[ExperimentResponseRow])
def list_experiment_responses(
    experiment_id: uuid.UUID, db: DbSession
) -> list[ExperimentResponseRow]:
    require_experiment(db, experiment_id)
    responses = (
        db.execute(
            select(ModelResponse)
            .where(ModelResponse.experiment_id == experiment_id)
            .order_by(ModelResponse.created_at.desc())
        )
        .scalars()
        .all()
    )
    return [serialize_response_row(response) for response in responses]


@router.get("/experiments/{experiment_id}/failures", response_model=list[ExperimentFailureRow])
def list_experiment_failures(
    experiment_id: uuid.UUID, db: DbSession
) -> list[ExperimentFailureRow]:
    return [
        row
        for row in (
            serialize_failure_row(response)
            for response in (
                db.execute(
                    select(ModelResponse)
                    .where(ModelResponse.experiment_id == experiment_id)
                    .order_by(ModelResponse.created_at.desc())
                )
                .scalars()
                .all()
            )
        )
        if row is not None
    ]


@router.get("/responses/{model_response_id}/trace", response_model=ResponseTraceRead)
def get_response_trace(model_response_id: uuid.UUID, db: DbSession) -> ResponseTraceRead:
    response = require_response(db, model_response_id)
    return serialize_response_trace(response)


@router.get("/experiments/{experiment_id}/report", response_model=ExperimentReport)
def get_experiment_report(experiment_id: uuid.UUID, db: DbSession) -> ExperimentReport:
    experiment = require_experiment(db, experiment_id)
    results = experiment_service.aggregate_results(db, experiment_id)
    failures = list_experiment_failures(experiment_id, db)
    generated_at = datetime.now(UTC)
    disclaimer = (
        "This report is computed from the connected local database. Synthetic sample data, "
        "deterministic providers, and MVP heuristic evaluators are not validated benchmarks "
        "or clinical evidence."
    )
    markdown = build_markdown_report(experiment, results, failures, generated_at, disclaimer)
    return ExperimentReport(
        experiment=serialize_experiment(experiment),
        results=results,
        failure_examples=failures[:10],
        markdown=markdown,
        generated_at=generated_at,
        disclaimer=disclaimer,
        metadata={
            "failure_type_counts": dict(Counter(row.failure_type or "unknown" for row in failures)),
            "report_type": "computed_markdown_json",
        },
    )


def require_experiment(db: Session, experiment_id: uuid.UUID) -> Experiment:
    experiment = db.get(Experiment, experiment_id)
    if experiment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")
    return experiment


def require_response(db: Session, model_response_id: uuid.UUID) -> ModelResponse:
    response = db.get(ModelResponse, model_response_id)
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model response not found",
        )
    return response


def latest_evaluation(response: ModelResponse) -> EvaluationResult | None:
    if not response.evaluation_results:
        return None
    return sorted(response.evaluation_results, key=lambda item: item.created_at, reverse=True)[0]


def serialize_response_row(response: ModelResponse) -> ExperimentResponseRow:
    evaluation = latest_evaluation(response)
    return ExperimentResponseRow(
        response_id=response.id,
        qa_example_id=response.qa_example_id,
        question=response.qa_example.question,
        expected_answerability=response.qa_example.answerability,
        model_answerability=response.answerability,
        answer_text=response.answer_text,
        correctness_score=evaluation.correctness_score if evaluation else None,
        groundedness_score=evaluation.groundedness_score if evaluation else None,
        hallucination_flag=evaluation.hallucination_flag if evaluation else None,
        failure_type=evaluation.failure_type if evaluation else None,
        created_at=response.created_at,
    )


def serialize_failure_row(response: ModelResponse) -> ExperimentFailureRow | None:
    row = serialize_response_row(response)
    if row.failure_type in {None, "none"} and not row.hallucination_flag:
        return None
    return ExperimentFailureRow(**row.model_dump(), failure_reason=row.failure_type or "flagged")


def serialize_response_trace(response: ModelResponse) -> ResponseTraceRead:
    evaluation = latest_evaluation(response)
    chunks = [serialize_trace_chunk(trace_chunk) for trace_chunk in response.retrieved_chunks]
    cited = [chunk for chunk in chunks if chunk.was_cited]
    prompt = response.prompt_template
    return ResponseTraceRead(
        model_response=serialize_model_response(response),
        qa_example=serialize_qa_example(response.qa_example),
        experiment=serialize_experiment(response.experiment) if response.experiment else None,
        evaluation=serialize_evaluation_result(evaluation) if evaluation else None,
        retrieved_chunks=sorted(chunks, key=lambda chunk: chunk.rank),
        cited_chunks=sorted(cited, key=lambda chunk: chunk.rank),
        prompt_template=PromptTemplateSummary(
            id=prompt.id,
            name=prompt.name,
            version=prompt.version,
            template_type=prompt.template_type,
        )
        if prompt
        else None,
    )


def serialize_trace_chunk(trace_chunk: ResponseRetrievedChunk) -> TraceChunkRead:
    chunk = trace_chunk.chunk
    return TraceChunkRead(
        chunk_id=chunk.id,
        document_id=chunk.document_id,
        document_title=chunk.document.title,
        chunk_index=chunk.chunk_index,
        chunk_text=chunk.chunk_text,
        rank=trace_chunk.rank,
        similarity_score=trace_chunk.similarity_score,
        was_cited=trace_chunk.was_cited,
    )


def build_markdown_report(
    experiment: Experiment,
    results,
    failures: list[ExperimentFailureRow],
    generated_at: datetime,
    disclaimer: str,
) -> str:
    failure_counts = Counter(row.failure_type or "unknown" for row in failures)
    lines = [
        f"# MedEval Experiment Report: {experiment.name}",
        "",
        f"Generated: {generated_at.isoformat()}",
        "",
        "## Disclaimer",
        "",
        disclaimer,
        "",
        "## Experiment Config",
        "",
        f"- Status: {experiment.status}",
        f"- Model: {experiment.model_provider} / {experiment.model_name}",
        f"- Retrieval: {experiment.retrieval_strategy}, top_k={experiment.top_k}",
        f"- Embedding model: {experiment.embedding_model}",
        "",
        "## Aggregate Metrics",
        "",
        f"- Examples: {results.example_count}",
        f"- Avg correctness: {format_metric(results.avg_correctness)}",
        f"- Avg groundedness: {format_metric(results.avg_groundedness)}",
        f"- Citation precision: {format_metric(results.avg_citation_precision)}",
        f"- Citation recall: {format_metric(results.avg_citation_recall)}",
        f"- Retrieval recall: {format_metric(results.avg_retrieval_recall)}",
        f"- Refusal accuracy: {format_metric(results.refusal_accuracy)}",
        f"- Hallucination rate: {format_metric(results.hallucination_rate)}",
        "",
        "## Failure Counts",
        "",
    ]
    if failure_counts:
        lines.extend(f"- {failure_type}: {count}" for failure_type, count in failure_counts.items())
    else:
        lines.append("- No failure rows found for this experiment.")
    lines.extend(["", "## Representative Failure Examples", ""])
    if failures:
        for failure in failures[:5]:
            lines.extend(
                [
                    f"### {failure.failure_type or 'flagged'}",
                    "",
                    f"Question: {failure.question}",
                    "",
                    f"Answer: {failure.answer_text}",
                    "",
                ]
            )
    else:
        lines.append("No representative failures available.")
    return "\n".join(lines)


def format_metric(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f}"
