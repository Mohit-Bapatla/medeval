from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.model_response import ModelResponse
from app.models.qa_example import QAExample
from app.services.evaluation_service import evaluation_service
from tests.batch2_helpers import create_dataset_with_example_and_evidence


def test_evaluation_metrics_for_rag_response(client: TestClient) -> None:
    _, example_id, _ = create_dataset_with_example_and_evidence(client)
    rag = client.post("/api/v1/rag/answer", json={"qa_example_id": example_id, "top_k": 3}).json()
    response_id = rag["model_response"]["id"]

    evaluation = client.post(f"/api/v1/responses/{response_id}/evaluate")

    assert evaluation.status_code == 200
    payload = evaluation.json()
    assert payload["retrieval_recall"] == 1.0
    assert payload["citation_recall"] == 1.0
    assert payload["citation_precision"] == 1.0
    assert payload["hallucination_flag"] is False
    assert payload["failure_type"] in {"none", "partial_answer"}


def test_evaluation_flags_unanswerable_substantive_answer(client: TestClient) -> None:
    dataset = client.post("/api/v1/datasets", json={"name": "Unanswerable QA"}).json()
    example = client.post(
        f"/api/v1/datasets/{dataset['id']}/examples",
        json={
            "question": "Does the source specify housing?",
            "gold_answer": "The provided sources do not specify housing.",
            "answerability": "unanswerable",
        },
    ).json()
    # This exercises the unanswerable/refusal evaluator path with no retrieved evidence.
    response = client.post(
        "/api/v1/rag/answer",
        json={"qa_example_id": example["id"], "question": "housing", "top_k": 1},
    )
    assert response.status_code == 200
    model_response_id = response.json()["model_response"]["id"]
    evaluation = client.post(f"/api/v1/responses/{model_response_id}/evaluate").json()
    assert evaluation["refusal_score"] == 1.0
    assert evaluation["hallucination_flag"] is False


def test_evaluation_flags_failed_refusal_as_hallucination(db_session: Session) -> None:
    dataset = Dataset(name="Synthetic direct eval", source="synthetic_demo")
    db_session.add(dataset)
    db_session.flush()
    example = QAExample(
        dataset_id=dataset.id,
        question="Does the source specify housing?",
        gold_answer="The provided sources do not specify housing.",
        answerability="unanswerable",
        category="benefits",
        difficulty="easy",
        risk_level="low",
    )
    db_session.add(example)
    db_session.flush()
    response = ModelResponse(
        qa_example_id=example.id,
        answer_text="Yes, housing is provided.",
        answerability="answerable",
        confidence=0.8,
        cited_chunk_ids_json=[],
        retrieved_chunk_ids_json=[],
        raw_model_output={},
        model_provider="deterministic_local",
        model_name="direct-test",
    )
    db_session.add(response)
    db_session.commit()

    result = evaluation_service.evaluate(db_session, response.id)

    assert result.refusal_score == 0.0
    assert result.hallucination_flag is True
    assert result.failure_type == "failed_to_refuse"
    assert result.metadata_json["failure_taxonomy"]["primary_failure_category"] == (
        "failed_refusal"
    )
    assert result.metadata_json["failure_taxonomy"]["severity"] == "critical"
