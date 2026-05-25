"""Seed the synthetic QA sample dataset into the configured MedEval database."""

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.session import SessionLocal  # noqa: E402
from app.models.dataset import Dataset  # noqa: E402
from app.models.qa_example import QAExample  # noqa: E402
from app.schemas.datasets import DatasetCreate  # noqa: E402
from app.services.dataset_service import dataset_service  # noqa: E402
from app.services.qa_import_service import qa_import_service  # noqa: E402
from sqlalchemy import select  # noqa: E402


def main() -> None:
    qa_path = REPO_ROOT / "datasets" / "sample" / "qa" / "healthcare_qa_sample.jsonl"
    with SessionLocal() as db:
        dataset = (
            db.execute(select(Dataset).where(Dataset.name == "MedEval HealthcareQA Sample"))
            .scalars()
            .first()
        )
        if dataset is None:
            dataset = dataset_service.create_dataset(
                db,
                DatasetCreate(
                    name="MedEval HealthcareQA Sample",
                    description="Fictional QA examples for local MedEval development.",
                    source="synthetic_demo",
                    metadata={
                        "sample_file": str(qa_path.relative_to(REPO_ROOT)),
                        "synthetic": True,
                    },
                ),
            )
        dataset_id = dataset.id
        existing_example = (
            db.execute(select(QAExample).where(QAExample.dataset_id == dataset_id))
            .scalars()
            .first()
        )
        if existing_example is not None:
            print(
                f"Dataset {dataset_id} already has QA examples; skipping import. "
                "Use a fresh database or delete the dataset to reseed."
            )
            return
        result = qa_import_service.import_jsonl(db, dataset_id, qa_path.read_text(encoding="utf-8"))
        print(
            "Seeded dataset "
            f"{dataset_id}: {result.imported_examples} examples, "
            f"{result.evidence_links_created} evidence links, "
            f"{result.skipped_evidence_links} skipped evidence links"
        )


if __name__ == "__main__":
    main()
