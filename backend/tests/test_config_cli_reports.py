import json

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from typer.testing import CliRunner

import app.cli as cli_module
from app.db.base import Base
from app.models.qa_example import QAExample
from app.services.config_service import config_service
from tests.batch2_helpers import create_dataset_with_example_and_evidence


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


def test_cli_help_smoke() -> None:
    runner = CliRunner()
    result = runner.invoke(cli_module.app, ["--help"])
    assert result.exit_code == 0
    assert "MedEval deterministic local development CLI" in result.output


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
