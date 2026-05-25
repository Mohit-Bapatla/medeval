import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.experiments import ExperimentAggregateResults


class DashboardCounts(BaseModel):
    documents: int
    chunks: int
    datasets: int
    qa_examples: int
    experiments: int
    model_responses: int
    evaluation_results: int


class LatestExperimentSummary(BaseModel):
    id: uuid.UUID
    name: str
    status: str
    created_at: datetime
    results: ExperimentAggregateResults


class DashboardSummary(BaseModel):
    counts: DashboardCounts
    latest_experiment: LatestExperimentSummary | None
    status_note: str
