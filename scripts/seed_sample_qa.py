"""Seed the synthetic QA sample dataset into the configured MedEval database."""

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.session import SessionLocal  # noqa: E402
from app.schemas.datasets import DatasetCreate  # noqa: E402
from app.services.dataset_service import dataset_service  # noqa: E402
from app.services.qa_import_service import qa_import_service  # noqa: E402


def main() -> None:
    qa_path = REPO_ROOT / "datasets" / "sample" / "qa" / "healthcare_qa_sample.jsonl"
    with SessionLocal() as db:
        dataset = dataset_service.create_dataset(
            db,
            DatasetCreate(
                name="MedEval HealthcareQA Sample",
                description="Fictional QA examples for local MedEval development.",
                source="synthetic_demo",
                metadata={"sample_file": str(qa_path.relative_to(REPO_ROOT)), "synthetic": True},
            ),
        )
        result = qa_import_service.import_jsonl(db, dataset.id, qa_path.read_text(encoding="utf-8"))
        print(
            "Seeded dataset "
            f"{dataset.id}: {result.imported_examples} examples, "
            f"{result.evidence_links_created} evidence links, "
            f"{result.skipped_evidence_links} skipped evidence links"
        )


if __name__ == "__main__":
    main()
