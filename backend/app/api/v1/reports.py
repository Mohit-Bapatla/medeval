import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.datasets import serialize_qa_example
from app.api.v1.evaluations import serialize_evaluation_result
from app.api.v1.experiments import serialize_experiment
from app.api.v1.human_reviews import serialize_human_review
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
from app.services.report_export_service import report_export_service

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


@router.get("/experiments/{experiment_id}/report", response_model=None)
def get_experiment_report(
    experiment_id: uuid.UUID,
    db: DbSession,
    format: str = Query(default="json", pattern="^(json|markdown)$"),
):
    require_experiment(db, experiment_id)
    report = build_experiment_report(db, experiment_id)
    if format == "markdown":
        return Response(content=report.markdown, media_type="text/markdown")
    return report


@router.get("/experiments/{experiment_id}/results.csv")
def get_experiment_results_csv(experiment_id: uuid.UUID, db: DbSession) -> Response:
    require_experiment(db, experiment_id)
    rows = report_export_service.response_rows(db, experiment_id)
    return Response(
        content=report_export_service.csv(rows),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="experiment_{experiment_id}_results.csv"'
        },
    )


def build_experiment_report(db: Session, experiment_id: uuid.UUID) -> ExperimentReport:
    export = report_export_service.build_report(db, experiment_id)
    experiment = export["experiment"]
    results = export["results"]
    failures = list_experiment_failures(experiment_id, db)
    return ExperimentReport(
        experiment=serialize_experiment(experiment),
        results=results,
        failure_examples=failures[:10],
        markdown=export["markdown"],
        generated_at=export["generated_at"],
        disclaimer=export["disclaimer"],
        metadata=export["metadata"],
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
    metadata = evaluation.metadata_json if evaluation else {}
    failure_analysis = metadata.get("failure_analysis", {}) if metadata else {}
    claim_support = metadata.get("claim_support", {}) if metadata else {}
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
        primary_failure_type=failure_analysis.get("primary_failure_type"),
        secondary_failure_types=failure_analysis.get("secondary_failure_types", []),
        failure_reason=failure_analysis.get("failure_reason"),
        retrieval_failure=failure_analysis.get("retrieval_failure"),
        generation_failure=failure_analysis.get("generation_failure"),
        claim_count=claim_support.get("claim_count"),
        claim_support_rate=claim_support.get("claim_support_rate"),
        unsupported_claim_rate=claim_support.get("unsupported_claim_rate"),
        created_at=response.created_at,
    )


def serialize_failure_row(response: ModelResponse) -> ExperimentFailureRow | None:
    row = serialize_response_row(response)
    if row.failure_type in {None, "none"} and not row.hallucination_flag:
        return None
    payload = row.model_dump()
    payload["failure_reason"] = row.failure_reason or row.failure_type or "flagged"
    return ExperimentFailureRow(**payload)


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
        human_reviews=[serialize_human_review(review) for review in response.human_reviews],
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


def format_metric(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f}"
