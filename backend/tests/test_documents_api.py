from fastapi.testclient import TestClient


def test_document_create_list_get_chunk_embed_and_delete_flow(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/documents",
        json={
            "title": "Synthetic Clinic Onboarding",
            "source_type": "synthetic_demo",
            "document_type": "onboarding_doc",
            "organization_name": "Demo Community Clinic",
            "raw_text": (
                "This synthetic onboarding guide requires HIPAA training, a badge form, "
                "and a volunteer orientation session. Applicants should bring a photo ID. "
            )
            * 8,
            "metadata": {"demo": True},
        },
    )
    assert create_response.status_code == 201
    document = create_response.json()

    list_response = client.get("/api/v1/documents")
    assert list_response.status_code == 200
    assert list_response.json()[0]["title"] == "Synthetic Clinic Onboarding"

    get_response = client.get(f"/api/v1/documents/{document['id']}")
    assert get_response.status_code == 200
    assert "HIPAA training" in get_response.json()["cleaned_text"]

    chunk_response = client.post(
        f"/api/v1/documents/{document['id']}/chunk",
        json={"chunk_size_chars": 300, "chunk_overlap_chars": 50, "min_chunk_chars": 80},
    )
    assert chunk_response.status_code == 200
    chunks = chunk_response.json()["chunks"]
    assert chunk_response.json()["chunks_created"] == len(chunks)
    assert chunks[0]["chunk_index"] == 0

    embed_response = client.post(f"/api/v1/documents/{document['id']}/embed", json={})
    assert embed_response.status_code == 200
    assert embed_response.json()["embedded_chunks"] == len(chunks)
    assert embed_response.json()["embedding_dimension"] == 384

    chunks_response = client.get(f"/api/v1/documents/{document['id']}/chunks")
    assert chunks_response.status_code == 200
    assert chunks_response.json()[0]["embedding_model"] == "deterministic-hash-embedding-384"

    delete_response = client.delete(f"/api/v1/documents/{document['id']}")
    assert delete_response.status_code == 204
    assert client.get(f"/api/v1/documents/{document['id']}").status_code == 404


def test_document_api_validation_errors(client: TestClient) -> None:
    response = client.post(
        "/api/v1/documents",
        json={
            "title": " ",
            "raw_text": " ",
        },
    )

    assert response.status_code == 422
