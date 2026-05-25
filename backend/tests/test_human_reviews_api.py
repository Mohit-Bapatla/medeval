from fastapi.testclient import TestClient

from tests.batch2_helpers import create_dataset_with_example_and_evidence


def _create_response(client: TestClient) -> str:
    dataset_id, _, _ = create_dataset_with_example_and_evidence(client)
    experiment = client.post(
        "/api/v1/experiments",
        json={"name": "Human review smoke", "dataset_id": dataset_id, "top_k": 3},
    ).json()
    run_response = client.post(f"/api/v1/experiments/{experiment['id']}/run")
    assert run_response.status_code == 200
    responses = client.get(f"/api/v1/experiments/{experiment['id']}/responses").json()
    return responses[0]["response_id"]


def test_human_review_create_and_list(client: TestClient) -> None:
    response_id = _create_response(client)

    empty = client.get(f"/api/v1/responses/{response_id}/human-reviews")
    assert empty.status_code == 200
    assert empty.json() == []

    created = client.post(
        f"/api/v1/responses/{response_id}/human-review",
        json={
            "reviewer_name": "Local reviewer",
            "reviewer_role": "developer",
            "correctness_label": "correct",
            "groundedness_label": "grounded",
            "refusal_label": "not_applicable",
            "notes": "Synthetic local review only.",
        },
    )
    assert created.status_code == 201
    assert created.json()["correctness_label"] == "correct"

    listed = client.get(f"/api/v1/responses/{response_id}/human-reviews")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    trace = client.get(f"/api/v1/responses/{response_id}/trace").json()
    assert trace["human_reviews"][0]["reviewer_role"] == "developer"
