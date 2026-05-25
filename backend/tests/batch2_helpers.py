from fastapi.testclient import TestClient


def create_document_with_chunks(
    client: TestClient, title: str, text: str
) -> tuple[str, list[dict]]:
    response = client.post(
        "/api/v1/documents",
        json={
            "title": title,
            "source_type": "synthetic_demo",
            "document_type": "onboarding_doc",
            "raw_text": text,
            "metadata": {"sample_file": f"datasets/sample/documents/{title}.md"},
        },
    )
    assert response.status_code == 201
    document_id = response.json()["id"]
    chunk_response = client.post(
        f"/api/v1/documents/{document_id}/chunk",
        json={"chunk_size_chars": 600, "chunk_overlap_chars": 50, "min_chunk_chars": 80},
    )
    assert chunk_response.status_code == 200
    embed_response = client.post(f"/api/v1/documents/{document_id}/embed", json={})
    assert embed_response.status_code == 200
    return document_id, chunk_response.json()["chunks"]


def create_dataset_with_example_and_evidence(client: TestClient) -> tuple[str, str, str]:
    _, chunks = create_document_with_chunks(
        client,
        "synthetic_hipaa_policy",
        (
            "Participants must complete HIPAA training before receiving badge access. "
            "The module includes privacy principles and reporting suspected privacy incidents. "
        )
        * 4,
    )
    dataset_response = client.post(
        "/api/v1/datasets",
        json={"name": "Synthetic QA", "source": "synthetic_demo"},
    )
    assert dataset_response.status_code == 201
    dataset_id = dataset_response.json()["id"]
    example_response = client.post(
        f"/api/v1/datasets/{dataset_id}/examples",
        json={
            "question": "Is HIPAA training required before badge access?",
            "gold_answer": (
                "Participants must complete HIPAA training before receiving badge access."
            ),
            "answerability": "answerable",
            "category": "hipaa_training",
            "difficulty": "easy",
            "risk_level": "medium",
        },
    )
    assert example_response.status_code == 201
    example_id = example_response.json()["id"]
    link_response = client.post(
        f"/api/v1/qa-examples/{example_id}/evidence-links",
        json={"chunk_id": chunks[0]["id"], "evidence_role": "required"},
    )
    assert link_response.status_code == 201
    return dataset_id, example_id, chunks[0]["id"]
