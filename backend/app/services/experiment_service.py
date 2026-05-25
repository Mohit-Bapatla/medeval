import uuid
from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evaluation_result import EvaluationResult
from app.models.experiment import Experiment
from app.models.model_response import ModelResponse
from app.models.qa_example import QAExample
from app.schemas.experiments import ExperimentAggregateResults, ExperimentCreate
from app.schemas.rag import RagAnswerRequest
from app.services.config_service import ExperimentConfig, config_service
from app.services.evaluation_service import evaluation_service
from app.services.rag_service import rag_service


class ExperimentService:
    def create_experiment(self, db: Session, payload: ExperimentCreate) -> Experiment:
        experiment = Experiment(
            name=payload.name,
            dataset_id=payload.dataset_id,
            description=payload.description,
            model_provider=payload.model_provider,
            model_name=payload.model_name,
            embedding_model=payload.embedding_model,
            prompt_template_id=payload.prompt_template_id,
            retrieval_strategy=payload.retrieval_strategy,
            top_k=payload.top_k,
            temperature=payload.temperature,
            status="draft",
            metadata_json=payload.metadata,
        )
        db.add(experiment)
        db.commit()
        db.refresh(experiment)
        return experiment

    def create_experiment_from_config(self, db: Session, config: ExperimentConfig) -> Experiment:
        return self.create_experiment(db, config_service.to_experiment_create(db, config))

    def list_experiments(self, db: Session) -> list[Experiment]:
        return db.execute(select(Experiment).order_by(Experiment.created_at.desc())).scalars().all()

    def run_experiment(self, db: Session, experiment: Experiment) -> tuple[int, int, int]:
        experiment.status = "running"
        db.commit()
        examples = (
            db.execute(
                select(QAExample)
                .where(QAExample.dataset_id == experiment.dataset_id)
                .order_by(QAExample.created_at)
            )
            .scalars()
            .all()
        )
        responses = 0
        evaluations = 0
        try:
            for example in examples:
                trace = rag_service.answer(
                    db,
                    RagAnswerRequest(
                        qa_example_id=example.id,
                        top_k=experiment.top_k,
                        experiment_id=experiment.id,
                        prompt_template_id=experiment.prompt_template_id,
                    ),
                )
                if trace.model_response:
                    responses += 1
                    evaluation_service.evaluate(db, trace.model_response.id)
                    evaluations += 1
            experiment.status = "completed"
            db.commit()
        except Exception:
            experiment.status = "failed"
            db.commit()
            raise
        return len(examples), responses, evaluations

    def aggregate_results(
        self, db: Session, experiment_id: uuid.UUID
    ) -> ExperimentAggregateResults:
        experiment = db.get(Experiment, experiment_id)
        if experiment is None:
            raise ValueError("Experiment not found")
        evaluations = (
            db.execute(
                select(EvaluationResult)
                .join(ModelResponse)
                .where(ModelResponse.experiment_id == experiment_id)
            )
            .scalars()
            .all()
        )
        responses = (
            db.execute(select(ModelResponse).where(ModelResponse.experiment_id == experiment_id))
            .scalars()
            .all()
        )
        failure_counts = Counter(result.failure_type or "unknown" for result in evaluations)
        return ExperimentAggregateResults(
            experiment_id=experiment.id,
            status=experiment.status,
            example_count=len(responses),
            avg_correctness=self._avg([result.correctness_score for result in evaluations]),
            avg_groundedness=self._avg([result.groundedness_score for result in evaluations]),
            avg_citation_precision=self._avg([result.citation_precision for result in evaluations]),
            avg_citation_recall=self._avg([result.citation_recall for result in evaluations]),
            avg_retrieval_precision=self._avg(
                [result.retrieval_precision for result in evaluations]
            ),
            avg_retrieval_recall=self._avg([result.retrieval_recall for result in evaluations]),
            refusal_accuracy=self._avg([result.refusal_score for result in evaluations]),
            hallucination_rate=self._avg(
                [1.0 if result.hallucination_flag else 0.0 for result in evaluations]
            ),
            failure_type_counts=dict(failure_counts),
            avg_latency_ms=self._avg([response.latency_ms for response in responses]),
            total_estimated_cost=sum(
                response.estimated_cost or 0.0 for response in responses
            )
            if responses
            else None,
        )

    @staticmethod
    def _avg(values: list[float | int | None]) -> float | None:
        available = [float(value) for value in values if value is not None]
        if not available:
            return None
        return sum(available) / len(available)


experiment_service = ExperimentService()
