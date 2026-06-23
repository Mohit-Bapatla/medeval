import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

import app.cli as cli_module
from app.datasets.validation import dataset_statistics, validate_dataset

REPO_ROOT = Path(__file__).resolve().parents[2]
MEDEVAL_V1_PATH = REPO_ROOT / "datasets" / "medeval-v1"


def _read_first_jsonl_record(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8").splitlines()[0])


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")


def test_medeval_v1_example_dataset_validates() -> None:
    result = validate_dataset(MEDEVAL_V1_PATH)

    assert result.ok, result.errors
    assert len(result.documents) == 14
    assert len(result.example_documents) == 1
    assert len(result.qa_examples) == 92
    assert len(result.example_qa_examples) == 3
    assert {example.qa_id for example in result.example_qa_examples} == {
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
    assert stats["qa_count"] == 92
    assert stats["example_qa_count"] == 3
    assert stats["qa_count_by_split"] == {
        "qa_eval.jsonl": 60,
        "qa_hard.jsonl": 15,
        "qa_refusal.jsonl": 17,
    }
    assert stats["refusal_count"] == 17
    assert stats["answerable_count"] == 75
    assert stats["qa_count_by_category"]["clinical_caution"] == 32
    assert stats["qa_count_by_answer_type"]["refusal"] == 17
    assert stats["source_types"]["public_health_guidance"] == 5
    assert stats["source_types"]["patient_education"] == 2
    assert stats["source_types"]["drug_device_safety"] == 2
    assert stats["source_types"]["insurance_program"] == 2
    assert stats["source_types"]["federal_policy"] == 2
    assert stats["source_types"]["clinical_trial"] == 1


def test_dataset_validation_rejects_unknown_category(tmp_path) -> None:
    dataset_path = tmp_path / "medeval-v1"
    shutil.copytree(MEDEVAL_V1_PATH, dataset_path)
    qa_path = dataset_path / "qa" / "qa_eval.jsonl"
    record = _read_first_jsonl_record(qa_path)
    record["category"] = "not_a_taxonomy_category"
    _write_jsonl(qa_path, [record])

    result = validate_dataset(dataset_path)

    assert result.ok is False
    assert any("Input should be" in error for error in result.errors)


def test_dataset_validation_rejects_evidence_offset_mismatch(tmp_path) -> None:
    dataset_path = tmp_path / "medeval-v1"
    shutil.copytree(MEDEVAL_V1_PATH, dataset_path)
    qa_path = dataset_path / "qa" / "qa_eval.jsonl"
    record = _read_first_jsonl_record(qa_path)
    record["gold_evidence_spans"][0]["start_char"] += 1
    _write_jsonl(qa_path, [record])

    result = validate_dataset(dataset_path)

    assert result.ok is False
    assert any("evidence offsets do not match text" in error for error in result.errors)


def test_dataset_validation_rejects_missing_gold_doc_id_for_answerable_qa(tmp_path) -> None:
    dataset_path = tmp_path / "medeval-v1"
    shutil.copytree(MEDEVAL_V1_PATH, dataset_path)
    qa_path = dataset_path / "qa" / "qa_eval.jsonl"
    record = _read_first_jsonl_record(qa_path)
    record["gold_doc_ids"] = []
    _write_jsonl(qa_path, [record])

    result = validate_dataset(dataset_path)

    assert result.ok is False
    assert any(
        "answerable examples must include at least one gold_doc_id" in error
        for error in result.errors
    )


def test_dataset_validation_rejects_refusal_without_unsupported_reason(tmp_path) -> None:
    dataset_path = tmp_path / "medeval-v1"
    shutil.copytree(MEDEVAL_V1_PATH, dataset_path)
    qa_path = dataset_path / "qa" / "qa_refusal.jsonl"
    record = _read_first_jsonl_record(qa_path)
    record["unsupported_reason"] = None
    _write_jsonl(qa_path, [record])

    result = validate_dataset(dataset_path)

    assert result.ok is False
    assert any(
        "requires_refusal examples must include unsupported_reason" in error
        for error in result.errors
    )


def test_dataset_validation_rejects_duplicate_qa_id_across_real_splits(tmp_path) -> None:
    dataset_path = tmp_path / "medeval-v1"
    shutil.copytree(MEDEVAL_V1_PATH, dataset_path)
    eval_path = dataset_path / "qa" / "qa_eval.jsonl"
    hard_path = dataset_path / "qa" / "qa_hard.jsonl"
    eval_record = _read_first_jsonl_record(eval_path)
    hard_record = _read_first_jsonl_record(hard_path)
    hard_record["qa_id"] = eval_record["qa_id"]
    _write_jsonl(hard_path, [hard_record])

    result = validate_dataset(dataset_path)

    assert result.ok is False
    assert any("real QA: duplicate qa_id values" in error for error in result.errors)


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
    assert '"qa_count": 92' in stats_result.output
    assert '"example_qa_count": 3' in stats_result.output
    assert '"document_count": 14' in stats_result.output
