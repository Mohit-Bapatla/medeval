from fastapi.testclient import TestClient

from tests.batch2_helpers import create_document_with_chunks


def test_jsonl_import_resolves_document_file_and_chunk_index(client: TestClient) -> None:
    _, chunks = create_document_with_chunks(
        client,
        "hospital_volunteer_program",
        "Applicants must be at least 16 years old. Guardian consent is required under 18. "
        * 4,
    )
    dataset_id = client.post("/api/v1/datasets", json={"name": "Import QA"}).json()["id"]
    jsonl = (
        '{"question":"What age is required?","gold_answer":"Applicants must be at least '
        '16 years old.","answerability":"answerable","evidence":[{"document_file":'
        '"hospital_volunteer_program.md","chunk_index":0,"evidence_role":"required"}]}\n'
    )

    response = client.post(
        f"/api/v1/datasets/{dataset_id}/import-jsonl",
        files={"file": ("sample.jsonl", jsonl, "application/x-ndjson")},
    )

    assert response.status_code == 200
    assert response.json()["imported_examples"] == 1
    assert response.json()["evidence_links_created"] == 1
    examples = client.get(f"/api/v1/datasets/{dataset_id}/examples").json()
    links = client.get(f"/api/v1/qa-examples/{examples[0]['id']}/evidence-links").json()
    assert links[0]["chunk_id"] == chunks[0]["id"]


def test_jsonl_export(client: TestClient) -> None:
    dataset_id = client.post("/api/v1/datasets", json={"name": "Export QA"}).json()["id"]
    client.post(
        f"/api/v1/datasets/{dataset_id}/examples",
        json={
            "question": "Does the source specify an acceptance rate?",
            "gold_answer": "The provided sources do not specify an acceptance rate.",
            "answerability": "unanswerable",
        },
    )

    response = client.get(f"/api/v1/datasets/{dataset_id}/export-jsonl")

    assert response.status_code == 200
    assert "acceptance rate" in response.text
