from fastapi.testclient import TestClient

from tests.batch2_helpers import create_dataset_with_example_and_evidence


def test_experiment_create_run_and_results(client: TestClient) -> None:
    dataset_id, _, _ = create_dataset_with_example_and_evidence(client)
    create_response = client.post(
        "/api/v1/experiments",
        json={"name": "Synthetic local run", "dataset_id": dataset_id, "top_k": 3},
    )
    assert create_response.status_code == 201
    experiment_id = create_response.json()["id"]

    run_response = client.post(f"/api/v1/experiments/{experiment_id}/run")

    assert run_response.status_code == 200
    assert run_response.json()["examples_run"] == 1
    assert run_response.json()["evaluations_created"] == 1

    results_response = client.get(f"/api/v1/experiments/{experiment_id}/results")
    assert results_response.status_code == 200
    results = results_response.json()
    assert results["example_count"] == 1
    assert results["hallucination_rate"] == 0.0
