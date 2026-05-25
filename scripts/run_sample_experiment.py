"""Run a small deterministic local experiment for the synthetic QA dataset."""

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import select  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
from app.models.dataset import Dataset  # noqa: E402
from app.schemas.experiments import ExperimentCreate  # noqa: E402
from app.services.experiment_service import experiment_service  # noqa: E402


def main() -> None:
    with SessionLocal() as db:
        dataset = (
            db.execute(
                select(Dataset).where(Dataset.name == "MedEval HealthcareQA Sample")
            )
            .scalars()
            .first()
        )
        if dataset is None:
            raise SystemExit("Sample QA dataset not found. Run scripts/seed_sample_qa.py first.")

        experiment = experiment_service.create_experiment(
            db,
            ExperimentCreate(
                name="Synthetic deterministic local QA run",
                dataset_id=dataset.id,
                description="Local deterministic Batch 2 smoke run; not a benchmark result.",
                metadata={"synthetic": True, "not_benchmark": True},
            ),
        )
        examples, responses, evaluations = experiment_service.run_experiment(db, experiment)
        summary = experiment_service.aggregate_results(db, experiment.id)
        print(
            f"Run complete: {examples} examples, {responses} responses, "
            f"{evaluations} evaluations"
        )
        print(summary.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
