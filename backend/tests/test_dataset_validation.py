import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

import app.cli as cli_module
from app.datasets.validation import dataset_statistics, validate_dataset

REPO_ROOT = Path(__file__).resolve().parents[2]
MEDEVAL_V1_PATH = REPO_ROOT / "datasets" / "medeval-v1"


def test_medeval_v1_example_dataset_validates() -> None:
    result = validate_dataset(MEDEVAL_V1_PATH)

    assert result.ok, result.errors
    assert len(result.documents) == 1
    assert len(result.qa_examples) == 3
    assert {example.qa_id for example in result.qa_examples} == {
        "qa_000001",
        "qa_000002",
        "qa_000003",
    }


def test_dataset_statistics_counts_refusal_and_taxonomy() -> None:
    stats = dataset_statistics(MEDEVAL_V1_PATH)

    assert stats["valid"] is True
    assert stats["document_count"] == 1
    assert stats["qa_count"] == 3
    assert stats["refusal_count"] == 1
    assert stats["categories"]["eligibility"] == 1
    assert stats["answer_types"]["refusal"] == 1


def test_dataset_validation_rejects_unknown_category(tmp_path) -> None:
    dataset_path = tmp_path / "medeval-v1"
    shutil.copytree(MEDEVAL_V1_PATH, dataset_path)
    qa_path = dataset_path / "qa" / "qa_eval.example.jsonl"
    record = json.loads(qa_path.read_text(encoding="utf-8").splitlines()[0])
    record["category"] = "not_a_taxonomy_category"
    qa_path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    result = validate_dataset(dataset_path)

    assert result.ok is False
    assert any("Input should be" in error for error in result.errors)


def test_cli_validate_dataset_and_stats_smoke() -> None:
    runner = CliRunner()

    validate_result = runner.invoke(
        cli_module.app,
        ["validate-dataset", "--path", str(MEDEVAL_V1_PATH)],
    )
    stats_result = runner.invoke(
        cli_module.app,
        ["dataset-stats", "--path", str(MEDEVAL_V1_PATH)],
    )

    assert validate_result.exit_code == 0, validate_result.output
    assert "Dataset valid" in validate_result.output
    assert stats_result.exit_code == 0, stats_result.output
    assert '"qa_count": 3' in stats_result.output
