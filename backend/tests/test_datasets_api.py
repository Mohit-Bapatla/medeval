from fastapi.testclient import TestClient


def test_dataset_create_list_get_delete(client: TestClient) -> None:
    response = client.post(
        "/api/v1/datasets",
        json={"name": "Synthetic Dataset", "description": "Demo only", "source": "synthetic_demo"},
    )
    assert response.status_code == 201
    dataset_id = response.json()["id"]

    assert client.get("/api/v1/datasets").json()[0]["name"] == "Synthetic Dataset"
    assert client.get(f"/api/v1/datasets/{dataset_id}").status_code == 200
    assert client.delete(f"/api/v1/datasets/{dataset_id}").status_code == 204
    assert client.get(f"/api/v1/datasets/{dataset_id}").status_code == 404


def test_qa_example_creation(client: TestClient) -> None:
    dataset = client.post("/api/v1/datasets", json={"name": "Synthetic QA"}).json()
    response = client.post(
        f"/api/v1/datasets/{dataset['id']}/examples",
        json={
            "question": "Does the source specify housing?",
            "gold_answer": "The provided sources do not specify housing.",
            "answerability": "unanswerable",
            "category": "benefits",
            "difficulty": "easy",
            "risk_level": "low",
        },
    )

    assert response.status_code == 201
    assert response.json()["answerability"] == "unanswerable"
    assert len(client.get(f"/api/v1/datasets/{dataset['id']}/examples").json()) == 1
