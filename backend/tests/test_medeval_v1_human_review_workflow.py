import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.human_review import HumanReview
from app.models.model_response import ModelResponse
from app.services.human_review_service import ReviewValidationError, human_review_service
from tests.batch2_helpers import create_dataset_with_example_and_evidence


def _run_experiment(client: TestClient) -> tuple[str, str]:
    dataset_id, _, _ = create_dataset_with_example_and_evidence(client)
    experiment = client.post(
        "/api/v1/experiments",
        json={"name": "Review workflow smoke", "dataset_id": dataset_id, "top_k": 3},
    ).json()
    run_response = client.post(f"/api/v1/experiments/{experiment['id']}/run")
    assert run_response.status_code == 200
    responses = client.get(f"/api/v1/experiments/{experiment['id']}/responses").json()
    return experiment["id"], responses[0]["response_id"]


def test_review_queue_api_includes_automated_rich_diagnostics(client: TestClient) -> None:
    experiment_id, _ = _run_experiment(client)

    response = client.get(f"/api/v1/human-reviews/queue?experiment_id={experiment_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["metadata"]["queue_type"] == "medeval_v1_manual_review_queue"
    assert payload["items"]
    item = payload["items"][0]
    assert "automated_scores" in item
    assert "rich_failure_taxonomy" in item
    assert "review_template" in item


def test_review_summary_api_works_with_zero_reviews(client: TestClient) -> None:
    experiment_id, _ = _run_experiment(client)

    response = client.get(f"/api/v1/human-reviews/summary?experiment_id={experiment_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["review_count"] == 0
    assert payload["completed_review_count"] == 0
    assert "not clinical validation" in payload["metadata"]["disclaimer"]


def test_api_save_review_and_summary_calibration(client: TestClient) -> None:
    experiment_id, response_id = _run_experiment(client)

    saved = client.put(
        f"/api/v1/human-reviews/responses/{response_id}",
        json={
            "reviewer_label": "sample_fixture_reviewer",
            "reviewer_type": "unknown",
            "answer_correctness": 3,
            "groundedness": 4,
            "citation_quality": 4,
            "refusal_safety": 5,
            "should_refuse": False,
            "did_refuse": False,
            "selected_failure_categories": ["incomplete_answer"],
            "severity_override": "medium",
            "review_notes": "Sample workflow test; not a real independent review.",
            "sample": True,
        },
    )
    assert saved.status_code == 200
    assert saved.json()["metadata"]["sample"] is True
    assert saved.json()["metadata"]["review_schema"] == "medeval_v1_manual_review"

    summary = client.get(f"/api/v1/human-reviews/summary?experiment_id={experiment_id}")
    assert summary.status_code == 200
    payload = summary.json()
    assert payload["completed_review_count"] == 1
    assert "incomplete_answer" in payload["reviewer_failure_category_counts"]
    assert "clinical validation" in payload["markdown"]


def test_review_validation_rejects_invalid_score_and_taxonomy_label() -> None:
    with pytest.raises(ReviewValidationError, match="answer_correctness"):
        human_review_service.validate_review_record(
            {
                "response_id": "00000000-0000-0000-0000-000000000000",
                "answer_correctness": 6,
            }
        )
    with pytest.raises(ValueError, match="Unknown failure category"):
        human_review_service.validate_review_record(
            {
                "response_id": "00000000-0000-0000-0000-000000000000",
                "answer_correctness": 5,
                "selected_failure_categories": ["not_a_real_category"],
            }
        )


def test_import_reviews_marks_sample_fixture(
    client: TestClient, db_session: Session, tmp_path: Path
) -> None:
    _, response_id = _run_experiment(client)
    fixture = {
        "reviews": [
            {
                "review_id": "sample_import_001",
                "response_id": response_id,
                "sample": True,
                "reviewer_type": "unknown",
                "answer_correctness": 4,
                "groundedness": 4,
                "citation_quality": 4,
                "refusal_safety": 5,
                "should_refuse": False,
                "did_refuse": False,
                "selected_failure_categories": ["incomplete_answer"],
                "severity_override": "medium",
                "review_notes": (
                    "Sample fixture for workflow testing; not a real independent "
                    "human review."
                ),
            }
        ]
    }
    fixture_path = tmp_path / "reviews.json"
    fixture_path.write_text(json.dumps(fixture), encoding="utf-8")

    result = human_review_service.import_reviews(
        db_session,
        fixture_path,
        reviewer_label="sample_fixture_reviewer",
    )

    assert result["imported"] == 1
    reviews = db_session.query(HumanReview).all()
    assert reviews[0].metadata_json["sample"] is True
    assert reviews[0].metadata_json["reviewer_label"] == "sample_fixture_reviewer"


def test_calibration_computes_category_overlap_jaccard(db_session: Session) -> None:
    response = ModelResponse(
        qa_example_id=create_dataset_with_example_and_evidence_for_db(db_session),
        answer_text="Synthetic answer",
        answerability="answerable",
        cited_chunk_ids_json=[],
        retrieved_chunk_ids_json=[],
        raw_model_output={},
        model_provider="deterministic_local",
        model_name="test",
    )
    db_session.add(response)
    db_session.flush()
    review = HumanReview(
        model_response_id=response.id,
        metadata_json={
            "review_schema": "medeval_v1_manual_review",
            "automated_failure_categories": ["bad_synthesis", "missing_citation"],
            "selected_failure_categories": ["bad_synthesis", "incomplete_answer"],
            "automated_severity": "high",
            "severity_override": "high",
            "should_refuse": True,
            "did_refuse": False,
        },
    )

    calibration = human_review_service.calibration_for_review(review)

    assert calibration["category_overlap_count"] == 1
    assert calibration["category_jaccard"] == pytest.approx(1 / 3)
    assert calibration["exact_category_match"] is False
    assert calibration["severity_match"] is True
    assert calibration["refusal_decision_match"] is False


def create_dataset_with_example_and_evidence_for_db(db_session: Session):
    from app.models.dataset import Dataset
    from app.models.qa_example import QAExample

    dataset = Dataset(name="Review calibration dataset", source="synthetic_demo")
    db_session.add(dataset)
    db_session.flush()
    example = QAExample(
        dataset_id=dataset.id,
        question="Synthetic question?",
        gold_answer="Synthetic answer",
        answerability="answerable",
        category="demo",
        difficulty="easy",
        risk_level="low",
        metadata_json={"qa_id": "review_calibration_001"},
    )
    db_session.add(example)
    db_session.flush()
    return example.id
