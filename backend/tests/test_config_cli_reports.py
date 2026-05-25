from typer.testing import CliRunner

from app.cli import app
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
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "MedEval deterministic local development CLI" in result.output
