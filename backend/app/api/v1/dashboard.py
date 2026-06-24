from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.dataset import Dataset
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.evaluation_result import EvaluationResult
from app.models.experiment import Experiment
from app.models.model_response import ModelResponse
from app.models.qa_example import QAExample
from app.schemas.dashboard import DashboardCounts, DashboardSummary, LatestExperimentSummary
from app.services.experiment_service import experiment_service

router = APIRouter(tags=["dashboard"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/dashboard/summary", response_model=DashboardSummary)
def get_dashboard_summary(db: DbSession) -> DashboardSummary:
    latest_experiment = (
        db.execute(select(Experiment).order_by(Experiment.created_at.desc()))
        .scalars()
        .first()
    )
    latest = None
    if latest_experiment is not None:
        latest = LatestExperimentSummary(
            id=latest_experiment.id,
            name=latest_experiment.name,
            status=latest_experiment.status,
            created_at=latest_experiment.created_at,
            results=experiment_service.aggregate_results(db, latest_experiment.id),
        )

    return DashboardSummary(
        counts=DashboardCounts(
            documents=count_rows(db, Document),
            chunks=count_rows(db, DocumentChunk),
            datasets=count_rows(db, Dataset),
            qa_examples=count_rows(db, QAExample),
            experiments=count_rows(db, Experiment),
            model_responses=count_rows(db, ModelResponse),
            evaluation_results=count_rows(db, EvaluationResult),
        ),
        latest_experiment=latest,
        status_note=(
            "Early development dashboard. Metrics reflect only the connected local database; "
            "seeded data may include the MedEval v1 public healthcare seed or synthetic demos. "
            "Results are not clinical validation."
        ),
    )


def count_rows(db: Session, model: type) -> int:
    return db.scalar(select(func.count()).select_from(model)) or 0
