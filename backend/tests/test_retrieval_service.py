from fastapi.testclient import TestClient


def _create_chunk_and_embed(client: TestClient, title: str, text: str, document_type: str) -> str:
    create_response = client.post(
        "/api/v1/documents",
        json={
            "title": title,
            "source_type": "synthetic_demo",
            "document_type": document_type,
            "raw_text": text,
            "metadata": {"test": True},
        },
    )
    assert create_response.status_code == 201
    document_id = create_response.json()["id"]

    chunk_response = client.post(
        f"/api/v1/documents/{document_id}/chunk",
        json={"chunk_size_chars": 500, "chunk_overlap_chars": 50, "min_chunk_chars": 80},
    )
    assert chunk_response.status_code == 200

    embed_response = client.post(f"/api/v1/documents/{document_id}/embed", json={})
    assert embed_response.status_code == 200
    return document_id


def test_retrieval_returns_relevant_chunks_near_top(client: TestClient) -> None:
    hipaa_doc_id = _create_chunk_and_embed(
        client,
        "Synthetic HIPAA Onboarding",
        (
            "HIPAA privacy training is required before volunteers receive badge access. "
            "The onboarding checklist includes confidentiality attestation and a photo ID. "
        )
        * 5,
        "onboarding_doc",
    )
    _create_chunk_and_embed(
        client,
        "Synthetic Research Assistant",
        (
            "The research assistant opportunity focuses on literature review, spreadsheet "
            "cleanup, and weekly study team meetings. "
        )
        * 5,
        "healthcare_opportunity",
    )

    response = client.post(
        "/api/v1/retrieval/search",
        json={"query": "HIPAA privacy training badge access", "top_k": 2},
    )

    assert response.status_code == 200
    results = response.json()["results"]
    assert results
    assert results[0]["document_id"] == hipaa_doc_id
    assert "HIPAA privacy training" in results[0]["chunk_text"]
    assert isinstance(results[0]["similarity_score"], float)


def test_retrieval_filter_by_document_type(client: TestClient) -> None:
    _create_chunk_and_embed(
        client,
        "Synthetic HIPAA Policy",
        "HIPAA training and confidentiality policy for synthetic volunteers. " * 5,
        "compliance_policy",
    )
    _create_chunk_and_embed(
        client,
        "Synthetic Clinic Listing",
        "Clinic volunteer opportunity with patient escort wayfinding and front desk support. " * 5,
        "volunteer_listing",
    )

    response = client.post(
        "/api/v1/retrieval/search",
        json={
            "query": "clinic volunteer front desk",
            "top_k": 5,
            "filters": {"document_type": "volunteer_listing"},
        },
    )

    assert response.status_code == 200
    assert response.json()["results"][0]["document_title"] == "Synthetic Clinic Listing"


def test_retrieval_validation_errors(client: TestClient) -> None:
    response = client.post("/api/v1/retrieval/search", json={"query": "test", "top_k": 0})

    assert response.status_code == 422
