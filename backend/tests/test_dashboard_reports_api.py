from fastapi.testclient import TestClient

from tests.batch2_helpers import create_dataset_with_example_and_evidence


def _run_experiment(client: TestClient) -> tuple[str, str]:
    dataset_id, _, _ = create_dataset_with_example_and_evidence(client)
    experiment = client.post(
        "/api/v1/experiments",
        json={"name": "Synthetic dashboard run", "dataset_id": dataset_id, "top_k": 3},
    ).json()
    run_response = client.post(f"/api/v1/experiments/{experiment['id']}/run")
    assert run_response.status_code == 200
    responses = client.get(f"/api/v1/experiments/{experiment['id']}/responses").json()
    return experiment["id"], responses[0]["response_id"]


def test_dashboard_summary_counts_empty_and_seeded(client: TestClient) -> None:
    empty = client.get("/api/v1/dashboard/summary")
    assert empty.status_code == 200
    assert empty.json()["counts"]["documents"] == 0

    _run_experiment(client)
    summary = client.get("/api/v1/dashboard/summary").json()

    assert summary["counts"]["documents"] == 1
    assert summary["counts"]["experiments"] == 1
    assert summary["latest_experiment"]["name"] == "Synthetic dashboard run"


def test_experiment_responses_failures_report_and_trace(client: TestClient) -> None:
    experiment_id, response_id = _run_experiment(client)

    responses = client.get(f"/api/v1/experiments/{experiment_id}/responses")
    assert responses.status_code == 200
    assert responses.json()[0]["question"] == "Is HIPAA training required before badge access?"

    failures = client.get(f"/api/v1/experiments/{experiment_id}/failures")
    assert failures.status_code == 200
    assert isinstance(failures.json(), list)

    trace = client.get(f"/api/v1/responses/{response_id}/trace")
    assert trace.status_code == 200
    trace_payload = trace.json()
    assert (
        trace_payload["qa_example"]["question"]
        == "Is HIPAA training required before badge access?"
    )
    assert trace_payload["retrieved_chunks"]
    assert trace_payload["evaluation"]["retrieval_recall"] == 1.0

    report = client.get(f"/api/v1/experiments/{experiment_id}/report")
    assert report.status_code == 200
    assert "MedEval Experiment Report" in report.json()["markdown"]
    assert "not validated benchmarks" in report.json()["disclaimer"]
