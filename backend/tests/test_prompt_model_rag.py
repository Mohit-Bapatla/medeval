from fastapi.testclient import TestClient

from app.services.model_provider_service import DeterministicAnswerProvider
from app.services.prompt_service import prompt_service
from app.services.retrieval_service import RetrievedChunk
from tests.batch2_helpers import create_dataset_with_example_and_evidence


def test_prompt_rendering() -> None:
    rendered = prompt_service.render_rag_prompt(
        "Is HIPAA training required?",
        [("chunk-1", "HIPAA training is required before badge access.")],
        "Question: {question}\nChunks:\n{source_chunks}",
    )

    assert "Is HIPAA training required?" in rendered
    assert "chunk-1" in rendered


def test_deterministic_answer_provider_returns_structured_output() -> None:
    provider = DeterministicAnswerProvider()
    chunk = RetrievedChunk(
        chunk_id="00000000-0000-0000-0000-000000000001",  # type: ignore[arg-type]
        document_id="00000000-0000-0000-0000-000000000002",  # type: ignore[arg-type]
        document_title="Synthetic HIPAA",
        chunk_index=0,
        chunk_text="Participants must complete HIPAA training before receiving badge access.",
        similarity_score=0.9,
        metadata={},
    )

    result = provider.answer("Is HIPAA training required before badge access?", [chunk], "prompt")

    assert result.answerability == "answerable"
    assert result.citations == ["00000000-0000-0000-0000-000000000001"]
    assert result.estimated_cost == 0.0


def test_rag_answer_creates_trace(client: TestClient) -> None:
    _, example_id, _ = create_dataset_with_example_and_evidence(client)

    response = client.post("/api/v1/rag/answer", json={"qa_example_id": example_id, "top_k": 3})

    assert response.status_code == 200
    payload = response.json()
    assert payload["model_response"]["qa_example_id"] == example_id
    assert payload["answer"]["answerability"] == "answerable"
    assert payload["response_retrieved_chunks"]
    assert payload["answer"]["citations"]
