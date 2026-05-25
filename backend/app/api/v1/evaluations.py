import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.evaluation_result import EvaluationResult
from app.schemas.evaluations import EvaluationResultRead
from app.services.evaluation_service import evaluation_service

router = APIRouter(tags=["evaluations"])
DbSession = Annotated[Session, Depends(get_db)]


@router.post("/responses/{model_response_id}/evaluate", response_model=EvaluationResultRead)
def evaluate_response(model_response_id: uuid.UUID, db: DbSession) -> EvaluationResultRead:
    try:
        result = evaluation_service.evaluate(db, model_response_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return serialize_evaluation_result(result)


@router.get("/responses/{model_response_id}/evaluation", response_model=EvaluationResultRead)
def get_response_evaluation(model_response_id: uuid.UUID, db: DbSession) -> EvaluationResultRead:
    result = (
        db.execute(
            select(EvaluationResult)
            .where(EvaluationResult.model_response_id == model_response_id)
            .order_by(EvaluationResult.created_at.desc())
        )
        .scalars()
        .first()
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")
    return serialize_evaluation_result(result)


def serialize_evaluation_result(result: EvaluationResult) -> EvaluationResultRead:
    return EvaluationResultRead(
        id=result.id,
        model_response_id=result.model_response_id,
        correctness_score=result.correctness_score,
        groundedness_score=result.groundedness_score,
        citation_precision=result.citation_precision,
        citation_recall=result.citation_recall,
        retrieval_precision=result.retrieval_precision,
        retrieval_recall=result.retrieval_recall,
        refusal_score=result.refusal_score,
        hallucination_flag=result.hallucination_flag,
        overall_score=result.overall_score,
        failure_type=result.failure_type,
        evaluator_name=result.evaluator_name,
        evaluator_version=result.evaluator_version,
        judge_explanation=result.judge_explanation,
        metadata=result.metadata_json,
        created_at=result.created_at,
    )
