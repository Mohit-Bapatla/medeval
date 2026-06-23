import json
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from typer.testing import CliRunner

import app.cli as cli_module
from app.db.base import Base
from app.models.document import Document
from app.models.evidence_link import EvidenceLink
from app.models.qa_example import QAExample
from app.services.config_service import config_service
from tests.batch2_helpers import create_dataset_with_example_and_evidence

REPO_ROOT = Path(__file__).resolve().parents[2]
MEDEVAL_V1_PATH = REPO_ROOT / "datasets" / "medeval-v1"
MEDEVAL_V1_CONFIG = REPO_ROOT / "configs" / "experiments" / "medeval_v1_deterministic.yaml"


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

    csv_response = client.get(f"/api/v1/experiments/{experiment['id']}/results.csv")
    assert csv_response.status_code == 200
    assert "response_id,qa_example_id,question" in csv_response.text


def test_medeval_v1_deterministic_config_parses() -> None:
    config = config_service.load_experiment_config(MEDEVAL_V1_CONFIG)

    assert config.name == "MedEval v1 Public Healthcare Seed - Deterministic Baseline"
    assert config.dataset_name == "MedEval v1 Public Healthcare Seed"
    assert config.model_provider == "deterministic_local"
    assert config.metadata["public_healthcare_seed"] is True
    assert config.metadata["not_clinically_validated"] is True


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
