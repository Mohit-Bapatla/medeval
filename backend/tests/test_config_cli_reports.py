import json
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from typer.testing import CliRunner

import app.cli as cli_module
from app.db.base import Base
from app.models.dataset import Dataset
from app.models.document import Document
from app.models.evaluation_result import EvaluationResult
from app.models.evidence_link import EvidenceLink
from app.models.experiment import Experiment
from app.models.model_response import ModelResponse
from app.models.qa_example import QAExample
from app.services.config_service import config_service
from tests.batch2_helpers import create_dataset_with_example_and_evidence

REPO_ROOT = Path(__file__).resolve().parents[2]
MEDEVAL_V1_PATH = REPO_ROOT / "datasets" / "medeval-v1"
MEDEVAL_V1_CONFIG = REPO_ROOT / "configs" / "experiments" / "medeval_v1_deterministic.yaml"
MEDEVAL_V1_CONFIG_VARIANTS = [
    REPO_ROOT / "configs" / "experiments" / "medeval_v1_deterministic_top3.yaml",
    REPO_ROOT / "configs" / "experiments" / "medeval_v1_deterministic_top8.yaml",
    REPO_ROOT / "configs" / "experiments" / "medeval_v1_deterministic_refusal_aware.yaml",
    REPO_ROOT / "configs" / "experiments" / "medeval_v1_deterministic_clean_context.yaml",
    REPO_ROOT / "configs" / "experiments" / "medeval_v1_deterministic_top5_clean_refusal.yaml",
]


def test_config_parse_and_experiment_from_config(client) -> None:
    dataset_id, _, _ = create_dataset_with_example_and_evidence(client)
    yaml_text = f"""
name: Config smoke run
dataset_id: {dataset_id}
model_provider: deterministic_local
model_name: deterministic-extractive-answer-v1
embedding_model: deterministic-hash-embedding-384
retrieval_strategy: vector_similarity
top_k: 3
temperature: 0.0
"""
    config = config_service.parse_experiment_yaml(yaml_text)
    assert config.name == "Config smoke run"

    response = client.post("/api/v1/experiments/from-config", json={"yaml_text": yaml_text})
    assert response.status_code == 201
    assert response.json()["name"] == "Config smoke run"


def test_report_markdown_and_csv_exports(client) -> None:
    dataset_id, _, _ = create_dataset_with_example_and_evidence(client)
    experiment = client.post(
        "/api/v1/experiments",
        json={"name": "Export smoke", "dataset_id": dataset_id, "top_k": 3},
    ).json()
    client.post(f"/api/v1/experiments/{experiment['id']}/run")

    markdown = client.get(f"/api/v1/experiments/{experiment['id']}/report?format=markdown")
    assert markdown.status_code == 200
    assert "not clinical validation" in markdown.text
    assert "Rich Failure Diagnostics" in markdown.text

    json_report = client.get(f"/api/v1/experiments/{experiment['id']}/report?format=json")
    assert json_report.status_code == 200
    assert "rich_failure_category_counts" in json_report.json()["metadata"]

    csv_response = client.get(f"/api/v1/experiments/{experiment['id']}/results.csv")
    assert csv_response.status_code == 200
    assert "response_id,qa_example_id,question" in csv_response.text
    assert "primary_failure_category" in csv_response.text
    assert "failure_categories" in csv_response.text


def test_medeval_v1_deterministic_config_parses() -> None:
    config = config_service.load_experiment_config(MEDEVAL_V1_CONFIG)

    assert config.name == "MedEval v1 Public Healthcare Seed - Deterministic Baseline"
    assert config.dataset_name == "MedEval v1 Public Healthcare Seed"
    assert config.model_provider == "deterministic_local"
    assert config.metadata["public_healthcare_seed"] is True
    assert config.metadata["not_clinically_validated"] is True


def test_medeval_v1_deterministic_variant_configs_parse() -> None:
    configs = [config_service.load_experiment_config(path) for path in MEDEVAL_V1_CONFIG_VARIANTS]

    assert {config.top_k for config in configs} == {3, 5, 8}
    assert any(config.metadata.get("deterministic_clean_context") for config in configs)
    assert any(config.metadata.get("deterministic_refusal_oracle") for config in configs)
    assert all(config.dataset_name == "MedEval v1 Public Healthcare Seed" for config in configs)


def test_cli_help_smoke() -> None:
    runner = CliRunner()
    result = runner.invoke(cli_module.app, ["--help"])
    assert result.exit_code == 0
    assert "MedEval deterministic local development CLI" in result.output


def test_cli_seed_dataset_imports_medeval_v1_real_splits(monkeypatch) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    monkeypatch.setattr(cli_module, "SessionLocal", testing_session_local)

    runner = CliRunner()
    first = runner.invoke(
        cli_module.app,
        [
            "seed-dataset",
            "--path",
            str(MEDEVAL_V1_PATH),
            "--dataset-name",
            "MedEval v1 Public Healthcare Seed",
        ],
    )
    second = runner.invoke(
        cli_module.app,
        [
            "seed-dataset",
            "--path",
            str(MEDEVAL_V1_PATH),
            "--dataset-name",
            "MedEval v1 Public Healthcare Seed",
        ],
    )

    assert first.exit_code == 0, first.output
    assert "Documents seeded: 14" in first.output
    assert "QA examples seeded: 92" in first.output
    assert "qa_eval.jsonl, qa_hard.jsonl, qa_refusal.jsonl" in first.output
    assert second.exit_code == 0, second.output
    assert "Documents seeded: 0; skipped existing: 14" in second.output
    assert "QA examples seeded: 0; skipped existing: 92" in second.output

    with testing_session_local() as db:
        assert db.scalar(select(func.count()).select_from(Document)) == 14
        assert db.scalar(select(func.count()).select_from(QAExample)) == 92
        assert db.scalar(select(func.count()).select_from(EvidenceLink)) > 75
        imported_ids = {
            row[0]
            for row in db.execute(select(QAExample.metadata_json["qa_id"].as_string())).all()
        }
        assert "qa_eval_000001" in imported_ids
        assert "qa_refusal_000001" in imported_ids
        assert "qa_000001" not in imported_ids

        example = (
            db.execute(
                select(QAExample).where(
                    QAExample.metadata_json["qa_id"].as_string() == "qa_eval_000001"
                )
            )
            .scalars()
            .one()
        )
        assert example.gold_answer
        assert example.metadata_json["answer_type"] == "extractive"
        assert example.metadata_json["gold_evidence_spans"]

        refusal = (
            db.execute(
                select(QAExample).where(
                    QAExample.metadata_json["qa_id"].as_string() == "qa_refusal_000001"
                )
            )
            .scalars()
            .one()
        )
        assert refusal.answerability == "unanswerable"
        assert refusal.metadata_json["requires_refusal"] is True
        assert refusal.metadata_json["unsupported_reason"] == "patient_specific_medical_advice"


def test_cli_compare_runs_exports_markdown_json_and_csv(monkeypatch, tmp_path) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    monkeypatch.setattr(cli_module, "SessionLocal", testing_session_local)

    with testing_session_local() as db:
        first_id = _create_completed_experiment(db, "Baseline", 0.30, 0.70, "retrieval_miss")
        second_id = _create_completed_experiment(db, "Clean Context", 0.45, 0.85, "none")

    runner = CliRunner()
    markdown_out = tmp_path / "comparison.md"
    json_out = tmp_path / "comparison.json"
    csv_out = tmp_path / "comparison.csv"
    base_args = [
        "compare-runs",
        "--experiment-id",
        str(first_id),
        "--experiment-id",
        str(second_id),
    ]

    markdown = runner.invoke(
        cli_module.app,
        [*base_args, "--format", "markdown", "--out", str(markdown_out)],
    )
    json_result = runner.invoke(
        cli_module.app,
        [*base_args, "--format", "json", "--out", str(json_out)],
    )
    csv_result = runner.invoke(
        cli_module.app,
        [*base_args, "--format", "csv", "--out", str(csv_out)],
    )

    assert markdown.exit_code == 0, markdown.output
    assert json_result.exit_code == 0, json_result.output
    assert csv_result.exit_code == 0, csv_result.output
    assert "not clinical validation" in markdown_out.read_text(encoding="utf-8")
    assert "Aggregate Metrics" in markdown_out.read_text(encoding="utf-8")
    parsed = json.loads(json_out.read_text(encoding="utf-8"))
    assert parsed["metadata"]["experiment_count"] == 2
    assert parsed["experiments"][1]["deltas_vs_baseline"]["avg_correctness_delta"] > 0
    assert parsed["experiments"][0]["rich_failure_category_counts"] == {
        "retrieval_miss": 1
    }
    csv_text = csv_out.read_text(encoding="utf-8")
    assert "experiment_id,experiment_id_short,name,status" in csv_text
    assert "correctness_delta" in csv_text
    assert "rich_failure_category_counts" in csv_text
    assert "retrieval_miss:1" in csv_text


def test_cli_compare_runs_rejects_unknown_or_noncompleted_experiments(
    monkeypatch, tmp_path
) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    monkeypatch.setattr(cli_module, "SessionLocal", testing_session_local)

    with testing_session_local() as db:
        completed_id = _create_completed_experiment(db, "Completed", 0.3, 0.7, "none")
        draft_id = _create_completed_experiment(db, "Draft", 0.2, 0.6, "none", status="draft")

    runner = CliRunner()
    unknown = runner.invoke(
        cli_module.app,
        [
            "compare-runs",
            "--experiment-id",
            str(completed_id),
            "--experiment-id",
            "00000000-0000-0000-0000-000000000000",
            "--out",
            str(tmp_path / "unknown.md"),
        ],
    )
    draft = runner.invoke(
        cli_module.app,
        [
            "compare-runs",
            "--experiment-id",
            str(completed_id),
            "--experiment-id",
            str(draft_id),
            "--out",
            str(tmp_path / "draft.md"),
        ],
    )

    assert unknown.exit_code == 1
    assert "Experiment not found" in unknown.output
    assert draft.exit_code == 1
    assert "requires completed experiments" in draft.output


def test_cli_seed_qa_does_not_access_detached_dataset(monkeypatch, tmp_path) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    monkeypatch.setattr(cli_module, "SessionLocal", testing_session_local)
    qa_path = tmp_path / "sample.jsonl"
    qa_path.write_text(
        json.dumps(
            {
                "question": "Is this synthetic?",
                "gold_answer": "Yes, this is synthetic demo data.",
                "answerability": "answerable",
                "category": "demo",
                "difficulty": "easy",
                "risk_level": "low",
                "metadata": {"synthetic": True},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    first = runner.invoke(
        cli_module.app,
        [
            "seed-qa",
            "--dataset-name",
            "MedEval HealthcareQA Sample",
            "--path",
            str(qa_path),
        ],
    )
    second = runner.invoke(
        cli_module.app,
        [
            "seed-qa",
            "--dataset-name",
            "MedEval HealthcareQA Sample",
            "--path",
            str(qa_path),
        ],
    )

    assert first.exit_code == 0, first.output
    assert "Seeded dataset" in first.output
    assert second.exit_code == 0, second.output
    assert "already has QA examples; skipping import" in second.output
    with testing_session_local() as db:
        examples = db.execute(select(QAExample)).scalars().all()
        assert len(examples) == 1


def _create_completed_experiment(
    db,
    name: str,
    correctness: float,
    retrieval_recall: float,
    failure_type: str,
    status: str = "completed",
):
    dataset = Dataset(name=f"{name} Dataset", source="synthetic_demo", metadata_json={})
    db.add(dataset)
    db.flush()
    example = QAExample(
        dataset_id=dataset.id,
        question=f"{name} question?",
        gold_answer=f"{name} answer",
        answerability="answerable",
        category="demo",
        difficulty="easy",
        risk_level="low",
        metadata_json={},
    )
    db.add(example)
    db.flush()
    experiment = Experiment(
        name=name,
        dataset_id=dataset.id,
        model_provider="deterministic_local",
        model_name="deterministic-extractive-answer-v1",
        embedding_model="deterministic-hash-embedding-384",
        retrieval_strategy="vector_similarity",
        top_k=5,
        temperature=0.0,
        status=status,
        metadata_json={"comparison_test": True},
    )
    db.add(experiment)
    db.flush()
    response = ModelResponse(
        experiment_id=experiment.id,
        qa_example_id=example.id,
        answer_text=f"{name} deterministic answer",
        answerability="answerable",
        confidence=0.8,
        cited_chunk_ids_json=[],
        retrieved_chunk_ids_json=[],
        raw_model_output={},
        latency_ms=12,
        estimated_cost=0.0,
        input_tokens=10,
        output_tokens=4,
        model_provider="deterministic_local",
        model_name="deterministic-extractive-answer-v1",
    )
    db.add(response)
    db.flush()
    db.add(
        EvaluationResult(
            model_response_id=response.id,
            correctness_score=correctness,
            groundedness_score=0.9,
            citation_precision=0.8,
            citation_recall=0.75,
            retrieval_precision=0.5,
            retrieval_recall=retrieval_recall,
            refusal_score=1.0,
            hallucination_flag=False,
            overall_score=0.8,
            failure_type=failure_type,
            evaluator_name="test-evaluator",
            evaluator_version="test",
            metadata_json={"claim_support": {}, "failure_analysis": {}},
        )
    )
    db.commit()
    return experiment.id
