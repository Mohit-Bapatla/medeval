import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.experiment import Experiment
from app.schemas.experiments import (
    ExperimentAggregateResults,
    ExperimentCreate,
    ExperimentFromConfigCreate,
    ExperimentRead,
    ExperimentRunResponse,
)
from app.services.config_service import config_service
from app.services.experiment_service import experiment_service

router = APIRouter(tags=["experiments"])
DbSession = Annotated[Session, Depends(get_db)]


@router.post("/experiments", response_model=ExperimentRead, status_code=status.HTTP_201_CREATED)
def create_experiment(payload: ExperimentCreate, db: DbSession) -> ExperimentRead:
    return serialize_experiment(experiment_service.create_experiment(db, payload))


@router.get("/experiments", response_model=list[ExperimentRead])
def list_experiments(db: DbSession) -> list[ExperimentRead]:
    experiments = experiment_service.list_experiments(db)
    return [serialize_experiment(experiment) for experiment in experiments]


@router.post("/experiments/from-config", response_model=ExperimentRead, status_code=201)
def create_experiment_from_config(
    payload: ExperimentFromConfigCreate, db: DbSession
) -> ExperimentRead:
    try:
        if payload.yaml_text:
            config = config_service.parse_experiment_yaml(payload.yaml_text)
        elif payload.config_path:
            from pathlib import Path

            config = config_service.load_experiment_config(Path(payload.config_path))
        else:
            raise ValueError("yaml_text or config_path is required")
        experiment = experiment_service.create_experiment_from_config(db, config)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return serialize_experiment(experiment)


@router.get("/experiments/{experiment_id}", response_model=ExperimentRead)
def get_experiment(experiment_id: uuid.UUID, db: DbSession) -> ExperimentRead:
    return serialize_experiment(require_experiment(db, experiment_id))


@router.post("/experiments/{experiment_id}/run", response_model=ExperimentRunResponse)
def run_experiment(experiment_id: uuid.UUID, db: DbSession) -> ExperimentRunResponse:
    experiment = require_experiment(db, experiment_id)
    examples, responses, evaluations = experiment_service.run_experiment(db, experiment)
    db.refresh(experiment)
    return ExperimentRunResponse(
        experiment=serialize_experiment(experiment),
        examples_run=examples,
        model_responses_created=responses,
        evaluations_created=evaluations,
    )


@router.get("/experiments/{experiment_id}/results", response_model=ExperimentAggregateResults)
def get_experiment_results(experiment_id: uuid.UUID, db: DbSession) -> ExperimentAggregateResults:
    try:
        return experiment_service.aggregate_results(db, experiment_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


def require_experiment(db: Session, experiment_id: uuid.UUID) -> Experiment:
    experiment = db.get(Experiment, experiment_id)
    if experiment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")
    return experiment


def serialize_experiment(experiment: Experiment) -> ExperimentRead:
    return ExperimentRead(
        id=experiment.id,
        name=experiment.name,
        dataset_id=experiment.dataset_id,
        description=experiment.description,
        model_provider=experiment.model_provider,
        model_name=experiment.model_name,
        embedding_model=experiment.embedding_model,
        prompt_template_id=experiment.prompt_template_id,
        retrieval_strategy=experiment.retrieval_strategy,
        top_k=experiment.top_k,
        temperature=experiment.temperature,
        status=experiment.status,  # type: ignore[arg-type]
        metadata=experiment.metadata_json,
        created_at=experiment.created_at,
        updated_at=experiment.updated_at,
    )
