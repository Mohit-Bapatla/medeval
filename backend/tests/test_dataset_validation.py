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
    assert len(result.documents) == 14
    assert len(result.example_documents) == 1
    assert len(result.qa_examples) == 3
    assert {example.qa_id for example in result.qa_examples} == {
        "qa_000001",
        "qa_000002",
        "qa_000003",
    }


def test_medeval_v1_real_document_metadata_is_complete() -> None:
    result = validate_dataset(MEDEVAL_V1_PATH)
    doc_ids = [document.doc_id for document in result.documents]
    allowed_source_types = {
        "public_health_guidance",
        "patient_education",
        "federal_policy",
        "clinical_trial",
        "drug_device_safety",
        "insurance_program",
    }

    assert len(doc_ids) == len(set(doc_ids))
    for document in result.documents:
        assert document.source_type in allowed_source_types
        assert document.publisher
        assert document.source_url
        assert document.license_notes
        assert (MEDEVAL_V1_PATH / document.document_path).exists()


def test_dataset_statistics_counts_real_docs_and_refusal_examples() -> None:
    stats = dataset_statistics(MEDEVAL_V1_PATH)

    assert stats["valid"] is True
    assert stats["document_count"] == 14
    assert stats["example_document_count"] == 1
    assert stats["qa_count"] == 3
    assert stats["refusal_count"] == 1
    assert stats["categories"]["eligibility"] == 1
    assert stats["answer_types"]["refusal"] == 1
    assert stats["source_types"]["public_health_guidance"] == 5
    assert stats["source_types"]["patient_education"] == 2
    assert stats["source_types"]["drug_device_safety"] == 2
    assert stats["source_types"]["insurance_program"] == 2
    assert stats["source_types"]["federal_policy"] == 2
    assert stats["source_types"]["clinical_trial"] == 1


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


def test_dataset_validation_rejects_duplicate_real_doc_id(tmp_path) -> None:
    dataset_path = tmp_path / "medeval-v1"
    shutil.copytree(MEDEVAL_V1_PATH, dataset_path)
    docs_path = dataset_path / "metadata" / "docs.json"
    records = json.loads(docs_path.read_text(encoding="utf-8"))
    records[1]["doc_id"] = records[0]["doc_id"]
    docs_path.write_text(json.dumps(records) + "\n", encoding="utf-8")

    result = validate_dataset(dataset_path)

    assert result.ok is False
    assert any("docs.json: duplicate doc_id values" in error for error in result.errors)


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
    assert '"document_count": 14' in stats_result.output
