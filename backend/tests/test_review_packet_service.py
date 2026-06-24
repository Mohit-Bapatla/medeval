import json
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy.orm import Session
from typer.testing import CliRunner

import app.cli as cli_module
from app.models.dataset import Dataset
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.evaluation_result import EvaluationResult
from app.models.evidence_link import EvidenceLink
from app.models.experiment import Experiment
from app.models.human_review import HumanReview
from app.models.model_response import ModelResponse, ResponseRetrievedChunk
from app.models.qa_example import QAExample
from app.services.review_packet_service import ReviewValidationError, review_packet_service


def test_export_review_packet_json_structure_and_failure_priority(
    db_session: Session,
) -> None:
    experiment_id = _create_packet_experiment(
        db_session,
        [
            _spec("low", ["incomplete_answer"], "medium", 0.7, "qa_eval.jsonl"),
            _spec("safety", ["failed_refusal"], "critical", 0.2, "qa_refusal.jsonl"),
        ],
    )

    packet = review_packet_service.build_packet(
        db_session,
        experiment_id,
        limit=2,
        strategy="failure_priority",
    )

    assert packet["packet_version"] == "medeval_review_packet_v1"
    assert packet["status"] == "pending_manual_review"
    assert "not completed human review" in packet["disclaimer"]
    assert packet["items"][0]["qa_id"] == "qa_safety"
    assert packet["items"][0]["rich_failure_categories"] == ["failed_refusal"]
    assert packet["items"][0]["manual_review"] == {
        "review_status": "pending",
        "reviewer_label": "",
        "reviewer_type": "unknown",
        "answer_correctness": None,
        "groundedness": None,
        "citation_quality": None,
        "refusal_safety": None,
        "should_refuse": None,
        "did_refuse": None,
        "selected_failure_categories": [],
        "severity_override": None,
        "confidence": None,
        "review_notes": "",
    }


def test_random_strategy_is_deterministic_with_seed(db_session: Session) -> None:
    experiment_id = _create_packet_experiment(
        db_session,
        [
            _spec("one", ["incomplete_answer"], "medium", 0.7, "qa_eval.jsonl"),
            _spec("two", ["retrieval_miss"], "high", 0.4, "qa_eval.jsonl"),
            _spec("three", ["citation_mismatch"], "medium", 0.5, "qa_hard.jsonl"),
            _spec("four", ["bad_synthesis"], "high", 0.2, "qa_refusal.jsonl"),
        ],
    )

    first = review_packet_service.build_packet(
        db_session,
        experiment_id,
        limit=4,
        strategy="random",
        seed=42,
    )
    second = review_packet_service.build_packet(
        db_session,
        experiment_id,
        limit=4,
        strategy="random",
        seed=42,
    )

    assert [item["response_id"] for item in first["items"]] == [
        item["response_id"] for item in second["items"]
    ]


def test_balanced_strategy_returns_category_mix(db_session: Session) -> None:
    experiment_id = _create_packet_experiment(
        db_session,
        [
            _spec("eligibility_a", ["incomplete_answer"], "medium", 0.7, "qa_eval.jsonl"),
            _spec("eligibility_b", ["retrieval_miss"], "high", 0.3, "qa_eval.jsonl"),
            _spec("privacy_a", ["unsupported_claim"], "high", 0.2, "qa_hard.jsonl"),
            _spec("refusal_a", ["failed_refusal"], "critical", 0.1, "qa_refusal.jsonl"),
        ],
    )

    packet = review_packet_service.build_packet(
        db_session,
        experiment_id,
        limit=3,
        strategy="balanced",
    )

    assert len({item["qa_category"] for item in packet["items"]}) >= 2
    assert len({item["expected_answerability"] for item in packet["items"]}) >= 2


def test_validate_review_packet_rejects_invalid_scores_and_taxonomy(
    db_session: Session,
    tmp_path: Path,
) -> None:
    experiment_id = _create_packet_experiment(
        db_session,
        [_spec("invalid", ["incomplete_answer"], "medium", 0.7, "qa_eval.jsonl")],
    )
    packet = review_packet_service.build_packet(db_session, experiment_id)
    packet_path = tmp_path / "packet.json"

    packet["items"][0]["manual_review"]["answer_correctness"] = 6
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    with pytest.raises(ReviewValidationError, match="answer_correctness"):
        review_packet_service.validate_packet(packet_path, db=db_session)

    packet["items"][0]["manual_review"]["answer_correctness"] = None
    packet["items"][0]["manual_review"]["selected_failure_categories"] = ["not_real"]
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    with pytest.raises(ReviewValidationError, match="Unknown failure category"):
        review_packet_service.validate_packet(packet_path, db=db_session)


def test_validate_review_packet_rejects_completed_without_label(
    db_session: Session,
    tmp_path: Path,
) -> None:
    experiment_id = _create_packet_experiment(
        db_session,
        [_spec("completed", ["incomplete_answer"], "medium", 0.7, "qa_eval.jsonl")],
    )
    packet = review_packet_service.build_packet(db_session, experiment_id)
    manual = packet["items"][0]["manual_review"]
    manual["review_status"] = "completed"
    manual["answer_correctness"] = 4
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")

    with pytest.raises(ReviewValidationError, match="completed review requires reviewer_label"):
        review_packet_service.validate_packet(packet_path, db=db_session)


def test_import_review_packet_skips_pending_and_imports_completed(
    db_session: Session,
    tmp_path: Path,
) -> None:
    experiment_id = _create_packet_experiment(
        db_session,
        [_spec("imported", ["incomplete_answer"], "medium", 0.7, "qa_eval.jsonl")],
    )
    packet = review_packet_service.build_packet(db_session, experiment_id)
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")

    pending = review_packet_service.import_packet(db_session, packet_path)

    assert pending == {
        "imported": 0,
        "updated": 0,
        "invalid": 0,
        "skipped_pending": 1,
    }
    assert db_session.query(HumanReview).count() == 0

    manual = packet["items"][0]["manual_review"]
    manual.update(
        {
            "review_status": "completed",
            "reviewer_label": "mohit_manual_review",
            "reviewer_type": "self",
            "answer_correctness": 4,
            "groundedness": 4,
            "citation_quality": 3,
            "refusal_safety": 5,
            "should_refuse": False,
            "did_refuse": False,
            "selected_failure_categories": ["incomplete_answer"],
            "severity_override": "medium",
            "confidence": 4,
            "review_notes": "Manual review test fixture.",
        }
    )
    packet_path.write_text(json.dumps(packet), encoding="utf-8")

    completed = review_packet_service.import_packet(db_session, packet_path)
    progress = review_packet_service.review_progress(db_session, experiment_id)

    assert completed["imported"] == 1
    assert completed["skipped_pending"] == 0
    assert progress["total_responses"] == 1
    assert progress["completed_reviews"] == 1
    assert progress["completion_percentage"] == 100.0
    assert progress["average_scores"]["answer_correctness"] == 4.0
    assert progress["reviewer_failure_category_counts"] == {"incomplete_answer": 1}


def test_review_progress_handles_zero_reviews(db_session: Session) -> None:
    experiment_id = _create_packet_experiment(
        db_session,
        [_spec("zero", ["retrieval_miss"], "high", 0.2, "qa_hard.jsonl")],
    )

    progress = review_packet_service.review_progress(db_session, experiment_id)

    assert progress["total_responses"] == 1
    assert progress["review_records"] == 0
    assert progress["completed_reviews"] == 0
    assert progress["pending_or_unreviewed"] == 1
    assert progress["calibration_available"] is False


def test_cli_review_packet_commands_smoke(
    db_session: Session,
    monkeypatch,
    tmp_path: Path,
) -> None:
    experiment_id = _create_packet_experiment(
        db_session,
        [_spec("cli", ["failed_refusal"], "critical", 0.1, "qa_refusal.jsonl")],
    )

    class _SessionFactory:
        def __call__(self):
            return db_session

    monkeypatch.setattr(cli_module, "SessionLocal", _SessionFactory())
    runner = CliRunner()
    packet_path = tmp_path / "packet.json"

    exported = runner.invoke(
        cli_module.app,
        [
            "export-review-packet",
            "--experiment-id",
            str(experiment_id),
            "--out",
            str(packet_path),
            "--format",
            "json",
            "--limit",
            "1",
            "--strategy",
            "failure_priority",
        ],
    )
    validated = runner.invoke(
        cli_module.app,
        ["validate-review-packet", "--path", str(packet_path)],
    )
    imported = runner.invoke(
        cli_module.app,
        [
            "import-review-packet",
            "--path",
            str(packet_path),
            "--reviewer-label",
            "mohit_manual_review",
        ],
    )
    progress = runner.invoke(
        cli_module.app,
        ["review-progress", "--experiment-id", str(experiment_id)],
    )

    assert exported.exit_code == 0, exported.output
    assert "1 pending items" in exported.output
    assert validated.exit_code == 0, validated.output
    assert "pending: 1" in validated.output
    assert imported.exit_code == 0, imported.output
    assert "skipped pending: 1" in imported.output
    assert progress.exit_code == 0, progress.output
    assert '"total_responses": 1' in progress.output


def _spec(
    suffix: str,
    categories: list[str],
    severity: str,
    correctness: float,
    split: str,
) -> dict[str, Any]:
    return {
        "suffix": suffix,
        "categories": categories,
        "severity": severity,
        "correctness": correctness,
        "split": split,
    }


def _create_packet_experiment(db: Session, specs: list[dict[str, Any]]):
    dataset = Dataset(name="Review packet dataset", source="synthetic_demo", metadata_json={})
    db.add(dataset)
    db.flush()
    experiment = Experiment(
        name="Review packet experiment",
        dataset_id=dataset.id,
        model_provider="deterministic_local",
        model_name="deterministic-extractive-answer-v1",
        embedding_model="deterministic-hash-embedding-384",
        retrieval_strategy="vector_similarity",
        top_k=3,
        temperature=0.0,
        status="completed",
        metadata_json={"review_packet_test": True},
    )
    db.add(experiment)
    db.flush()
    for index, spec in enumerate(specs):
        suffix = spec["suffix"]
        document = Document(
            title=f"Packet Source {suffix}",
            source_type="synthetic_demo",
            document_type="test_fixture",
            raw_text=f"Evidence text for {suffix}.",
            cleaned_text=f"Evidence text for {suffix}.",
            metadata_json={},
        )
        db.add(document)
        db.flush()
        chunk = DocumentChunk(
            document_id=document.id,
            chunk_index=0,
            chunk_text=f"Evidence text for {suffix}. This supports the expected answer.",
            token_count=12,
            char_start=0,
            char_end=60,
            embedding=[0.1] * 384,
            embedding_model="deterministic-hash-embedding-384",
            metadata_json={},
        )
        db.add(chunk)
        db.flush()
        category = "privacy_safety" if "failed_refusal" in spec["categories"] else "eligibility"
        answerability = "unanswerable" if "refusal" in spec["split"] else "answerable"
        qa = QAExample(
            dataset_id=dataset.id,
            document_id=document.id,
            question=f"Question {suffix}?",
            gold_answer=f"Expected answer {suffix}.",
            answerability=answerability,
            category=category,
            difficulty="hard" if spec["split"] != "qa_eval.jsonl" else "medium",
            risk_level="medium",
            metadata_json={"qa_id": f"qa_{suffix}", "split": spec["split"]},
        )
        db.add(qa)
        db.flush()
        db.add(EvidenceLink(qa_example_id=qa.id, chunk_id=chunk.id, evidence_role="required"))
        response = ModelResponse(
            experiment_id=experiment.id,
            qa_example_id=qa.id,
            answer_text=f"Generated answer {suffix}.",
            answerability="answerable",
            confidence=0.8,
            cited_chunk_ids_json=[str(chunk.id)] if index % 2 == 0 else [],
            retrieved_chunk_ids_json=[str(chunk.id)],
            raw_model_output={},
            latency_ms=10,
            estimated_cost=0.0,
            input_tokens=10,
            output_tokens=5,
            model_provider="deterministic_local",
            model_name="deterministic-extractive-answer-v1",
        )
        db.add(response)
        db.flush()
        db.add(
            ResponseRetrievedChunk(
                model_response_id=response.id,
                chunk_id=chunk.id,
                rank=1,
                similarity_score=0.9,
                was_cited=index % 2 == 0,
            )
        )
        db.add(
            EvaluationResult(
                model_response_id=response.id,
                correctness_score=spec["correctness"],
                groundedness_score=0.6,
                citation_precision=0.5,
                citation_recall=0.5,
                retrieval_precision=1.0,
                retrieval_recall=1.0,
                refusal_score=0.0 if answerability == "unanswerable" else 1.0,
                hallucination_flag=False,
                overall_score=spec["correctness"],
                failure_type=spec["categories"][0],
                evaluator_name="test-evaluator",
                evaluator_version="test",
                metadata_json={
                    "failure_taxonomy": {
                        "failure_categories": spec["categories"],
                        "failure_stage": "refusal"
                        if "failed_refusal" in spec["categories"]
                        else "generation",
                        "severity": spec["severity"],
                        "safety_relevant": spec["severity"] in {"high", "critical"},
                        "diagnostic_notes": [f"Diagnostic note for {suffix}."],
                    }
                },
            )
        )
    db.commit()
    return experiment.id
