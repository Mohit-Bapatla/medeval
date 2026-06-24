import csv
import io
import json
import uuid
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.evals.failure_taxonomy import failure_taxonomy
from app.models.evaluation_result import EvaluationResult
from app.models.experiment import Experiment
from app.models.human_review import HumanReview
from app.models.model_response import ModelResponse
from app.models.qa_example import QAExample

REVIEWER_TYPES = {"self", "student", "domain_reviewer", "clinician", "unknown"}
REVIEW_STATUSES = {"pending", "completed", "skipped"}
SEVERITIES = {"low", "medium", "high", "critical"}
ADJUDICATION_STATUSES = {"none", "needs_second_review", "adjudicated"}

REVIEW_DISCLAIMER = (
    "Manual review records are workflow artifacts for calibration against "
    "heuristic diagnostics. They are not clinical validation, medical advice, "
    "clinician review, production-use evidence, or benchmark validation. "
    "Sample fixtures are not real independent human review."
)


class ReviewValidationError(ValueError):
    pass


class HumanReviewService:
    def build_review_queue(self, db: Session, experiment_id: uuid.UUID) -> dict[str, Any]:
        experiment = self._get_experiment(db, experiment_id)
        responses = self._experiment_responses(db, experiment_id)
        return {
            "metadata": {
                "queue_type": "medeval_v1_manual_review_queue",
                "generated_at": datetime.now(UTC).isoformat(),
                "disclaimer": REVIEW_DISCLAIMER,
                "experiment_id": str(experiment.id),
                "experiment_name": experiment.name,
                "review_fields": self._blank_review_template(),
            },
            "experiment": self._experiment_payload(experiment),
            "items": [self._queue_item(response) for response in responses],
        }

    def import_reviews(
        self,
        db: Session,
        path: Path,
        reviewer_label: str | None = None,
        experiment_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        records = payload.get("reviews", payload if isinstance(payload, list) else [])
        if not isinstance(records, list):
            raise ReviewValidationError("Review import payload must contain a reviews list")

        imported = 0
        updated = 0
        skipped = 0
        errors: list[str] = []
        for index, record in enumerate(records):
            try:
                normalized = self.validate_review_record(
                    record,
                    reviewer_label=reviewer_label,
                )
                response = self._resolve_response(db, normalized, experiment_id)
                existing = self._find_existing_review(
                    db,
                    response.id,
                    normalized["reviewer_label"],
                    normalized.get("source_record_id") or normalized.get("review_id"),
                )
                if existing:
                    self._apply_review(existing, normalized)
                    updated += 1
                else:
                    db.add(self._new_review(response, normalized))
                    imported += 1
            except (ReviewValidationError, ValueError) as exc:
                skipped += 1
                errors.append(f"record {index}: {exc}")

        if errors:
            raise ReviewValidationError("; ".join(errors))
        db.commit()
        return {"imported": imported, "updated": updated, "skipped": skipped}

    def validate_review_record(
        self,
        record: dict[str, Any],
        reviewer_label: str | None = None,
    ) -> dict[str, Any]:
        if not isinstance(record, dict):
            raise ReviewValidationError("Review record must be an object")
        normalized = dict(record)
        normalized["reviewer_label"] = (
            reviewer_label
            or normalized.get("reviewer_label")
            or normalized.get("reviewer_id")
            or "unknown_reviewer"
        )
        normalized["reviewer_type"] = normalized.get("reviewer_type") or "unknown"
        if normalized["reviewer_type"] not in REVIEWER_TYPES:
            raise ReviewValidationError(f"Invalid reviewer_type: {normalized['reviewer_type']}")
        normalized["review_status"] = normalized.get("review_status") or "completed"
        if normalized["review_status"] not in REVIEW_STATUSES:
            raise ReviewValidationError(f"Invalid review_status: {normalized['review_status']}")
        for key in [
            "answer_correctness",
            "groundedness",
            "citation_quality",
            "refusal_safety",
            "confidence",
        ]:
            self._validate_score(normalized.get(key), key)
        categories = normalized.get("selected_failure_categories") or []
        if not isinstance(categories, list):
            raise ReviewValidationError("selected_failure_categories must be a list")
        for category in categories:
            failure_taxonomy.normalize_failure_category(category)
        severity = normalized.get("severity_override")
        if severity is not None and severity not in SEVERITIES:
            raise ReviewValidationError(f"Invalid severity_override: {severity}")
        adjudication = normalized.get("adjudication_status") or "none"
        if adjudication not in ADJUDICATION_STATUSES:
            raise ReviewValidationError(f"Invalid adjudication_status: {adjudication}")
        normalized["adjudication_status"] = adjudication
        for key in ["should_refuse", "did_refuse", "sample"]:
            if normalized.get(key) is not None and not isinstance(normalized[key], bool):
                raise ReviewValidationError(f"{key} must be boolean or null")
        return normalized

    def build_review_summary(self, db: Session, experiment_id: uuid.UUID) -> dict[str, Any]:
        experiment = self._get_experiment(db, experiment_id)
        responses = self._experiment_responses(db, experiment_id)
        reviews = [
            review
            for response in responses
            for review in response.human_reviews
            if self._review_metadata(review).get("review_schema") == "medeval_v1_manual_review"
        ]
        completed = [
            review
            for review in reviews
            if self._review_metadata(review).get("review_status") == "completed"
        ]
        rows = [self._summary_row(review) for review in completed]
        summary = {
            "metadata": {
                "summary_type": "medeval_v1_review_calibration",
                "generated_at": datetime.now(UTC).isoformat(),
                "disclaimer": REVIEW_DISCLAIMER,
                "experiment_id": str(experiment.id),
                "experiment_name": experiment.name,
            },
            "experiment": self._experiment_payload(experiment),
            "review_count": len(reviews),
            "completed_review_count": len(completed),
            "rubric_averages": self._rubric_averages(completed),
            "calibration": self._calibration_summary(rows),
            "reviewer_failure_category_counts": dict(
                Counter(
                    category
                    for row in rows
                    for category in row["selected_failure_categories"]
                )
            ),
            "reviewer_override_count": sum(1 for row in rows if row["has_override"]),
            "rows": rows,
            "limitations": [
                "Manual review workflow only; not clinical validation.",
                "Sample review fixtures are not real independent human review.",
                "Human review quality depends on reviewer expertise and rubric consistency.",
            ],
        }
        summary["markdown"] = self.review_summary_markdown(summary)
        return summary

    def review_summary_markdown(self, summary: dict[str, Any]) -> str:
        metadata = summary["metadata"]
        averages = summary["rubric_averages"]
        calibration = summary["calibration"]
        lines = [
            f"# MedEval v1 Review Calibration Summary: {metadata['experiment_name']}",
            "",
            f"Generated: {metadata['generated_at']}",
            "",
            "## Disclaimer",
            "",
            metadata["disclaimer"],
            "",
            "## Review Counts",
            "",
            f"- Review records: {summary['review_count']}",
            f"- Completed reviews: {summary['completed_review_count']}",
            "",
            "## Rubric Averages",
            "",
        ]
        if averages:
            lines.extend(f"- {key}: {value:.2f}" for key, value in sorted(averages.items()))
        else:
            lines.append("- No completed manual reviews yet.")
        lines.extend(
            [
                "",
                "## Automated Vs Manual Calibration",
                "",
                f"- Average category Jaccard: {calibration.get('avg_category_jaccard', 'n/a')}",
                f"- Exact category matches: {calibration.get('exact_category_match_count', 0)}",
                f"- Severity matches: {calibration.get('severity_match_count', 0)}",
                "- Refusal decision agreement: "
                f"{calibration.get('refusal_decision_agreement_rate', 'n/a')}",
                f"- Reviewer overrides: {summary['reviewer_override_count']}",
                "",
                "## Reviewer Failure Categories",
                "",
            ]
        )
        categories = summary["reviewer_failure_category_counts"]
        if categories:
            lines.extend(f"- {key}: {value}" for key, value in sorted(categories.items()))
        else:
            lines.append("- No reviewer-selected failure categories yet.")
        lines.extend(
            [
                "",
                "## Limitations",
                "",
                "- Manual reviews are workflow records, not benchmark validation.",
                "- Do not interpret sample fixtures as real independent human review.",
                "- This summary is not clinical validation, clinician review, or medical advice.",
            ]
        )
        return "\n".join(lines)

    def review_summary_csv(self, summary: dict[str, Any]) -> str:
        output = io.StringIO()
        fieldnames = [
            "review_id",
            "response_id",
            "reviewer_label",
            "reviewer_type",
            "review_status",
            "answer_correctness",
            "groundedness",
            "citation_quality",
            "refusal_safety",
            "should_refuse",
            "did_refuse",
            "automated_failure_categories",
            "selected_failure_categories",
            "category_overlap_count",
            "category_jaccard",
            "exact_category_match",
            "severity_match",
            "refusal_decision_match",
            "severity_override",
            "has_override",
            "sample",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in summary["rows"]:
            serializable = {
                key: ";".join(value) if isinstance(value, list) else value
                for key, value in row.items()
            }
            writer.writerow(serializable)
        return output.getvalue()

    def calibration_for_review(self, review: HumanReview) -> dict[str, Any]:
        metadata = self._review_metadata(review)
        automated = set(metadata.get("automated_failure_categories") or [])
        reviewer = set(metadata.get("selected_failure_categories") or [])
        union = automated.union(reviewer)
        automated_severity = metadata.get("automated_severity")
        severity_override = metadata.get("severity_override")
        should_refuse = metadata.get("should_refuse")
        did_refuse = metadata.get("did_refuse")
        return {
            "category_overlap_count": len(automated.intersection(reviewer)),
            "category_jaccard": len(automated.intersection(reviewer)) / len(union)
            if union
            else None,
            "exact_category_match": automated == reviewer,
            "severity_match": automated_severity == severity_override
            if automated_severity and severity_override
            else None,
            "refusal_decision_match": should_refuse == did_refuse
            if should_refuse is not None and did_refuse is not None
            else None,
        }

    def _queue_item(self, response: ModelResponse) -> dict[str, Any]:
        evaluation = self._latest_evaluation(response)
        taxonomy = self._failure_taxonomy(evaluation)
        return {
            "response_id": str(response.id),
            "evaluation_id": str(evaluation.id) if evaluation else None,
            "qa_example_id": str(response.qa_example_id),
            "qa_id": (response.qa_example.metadata_json or {}).get("qa_id"),
            "question": response.qa_example.question,
            "gold_answer": response.qa_example.gold_answer,
            "expected_answerability": response.qa_example.answerability,
            "generated_answer": response.answer_text,
            "model_answerability": response.answerability,
            "cited_chunk_ids": response.cited_chunk_ids_json,
            "retrieved_chunks": [
                {
                    "chunk_id": str(trace.chunk_id),
                    "rank": trace.rank,
                    "was_cited": trace.was_cited,
                    "document_title": trace.chunk.document.title,
                    "chunk_text": trace.chunk.chunk_text,
                }
                for trace in sorted(response.retrieved_chunks, key=lambda item: item.rank)
            ],
            "automated_scores": self._automated_scores(evaluation),
            "legacy_failure_type": evaluation.failure_type if evaluation else None,
            "rich_failure_taxonomy": taxonomy,
            "manual_review": self._manual_review_snapshot(response),
            "review_template": self._blank_review_template(),
        }

    def _manual_review_snapshot(self, response: ModelResponse) -> dict[str, Any] | None:
        reviews = [
            review
            for review in response.human_reviews
            if self._review_metadata(review).get("review_schema")
            == "medeval_v1_manual_review"
        ]
        if not reviews:
            return None
        review = sorted(
            reviews,
            key=lambda item: (item.updated_at, item.created_at),
            reverse=True,
        )[0]
        metadata = self._review_metadata(review)
        return {
            "review_id": str(review.id),
            "reviewer_label": metadata.get("reviewer_label"),
            "reviewer_type": metadata.get("reviewer_type"),
            "review_status": metadata.get("review_status"),
            "answer_correctness": metadata.get("answer_correctness"),
            "groundedness": metadata.get("groundedness"),
            "citation_quality": metadata.get("citation_quality"),
            "refusal_safety": metadata.get("refusal_safety"),
            "should_refuse": metadata.get("should_refuse"),
            "did_refuse": metadata.get("did_refuse"),
            "selected_failure_categories": metadata.get("selected_failure_categories", []),
            "severity_override": metadata.get("severity_override"),
            "review_notes": metadata.get("review_notes"),
            "confidence": metadata.get("confidence"),
            "reviewer_time_seconds": metadata.get("reviewer_time_seconds"),
            "adjudication_status": metadata.get("adjudication_status"),
            "sample": metadata.get("sample", False),
            "sample_notes": metadata.get("sample_notes"),
        }

    def _blank_review_template(self) -> dict[str, Any]:
        return {
            "reviewer_label": None,
            "reviewer_type": "unknown",
            "review_status": "pending",
            "answer_correctness": None,
            "groundedness": None,
            "citation_quality": None,
            "refusal_safety": None,
            "should_refuse": None,
            "did_refuse": None,
            "selected_failure_categories": [],
            "severity_override": None,
            "review_notes": None,
            "confidence": None,
            "reviewer_time_seconds": None,
            "adjudication_status": "none",
        }

    def _new_review(self, response: ModelResponse, normalized: dict[str, Any]) -> HumanReview:
        review = HumanReview(model_response_id=response.id, model_response=response)
        self._apply_review(review, normalized)
        return review

    def _apply_review(self, review: HumanReview, normalized: dict[str, Any]) -> None:
        metadata = dict(review.metadata_json or {})
        metadata.update(self._metadata_payload(review, normalized))
        review.reviewer_name = normalized["reviewer_label"]
        review.reviewer_role = normalized["reviewer_type"]
        review.correctness_label = self._score_label(normalized.get("answer_correctness"))
        review.groundedness_label = self._groundedness_label(normalized.get("groundedness"))
        review.refusal_label = self._refusal_label(normalized)
        review.notes = normalized.get("review_notes") or normalized.get("notes")
        review.metadata_json = metadata

    def _metadata_payload(
        self, review: HumanReview, normalized: dict[str, Any]
    ) -> dict[str, Any]:
        response = review.model_response
        automated = self._automated_snapshot(response) if response else {}
        return {
            "review_schema": "medeval_v1_manual_review",
            "source_record_id": normalized.get("review_id") or normalized.get("source_record_id"),
            "reviewer_label": normalized["reviewer_label"],
            "reviewer_type": normalized["reviewer_type"],
            "review_status": normalized["review_status"],
            "answer_correctness": normalized.get("answer_correctness"),
            "groundedness": normalized.get("groundedness"),
            "citation_quality": normalized.get("citation_quality"),
            "refusal_safety": normalized.get("refusal_safety"),
            "should_refuse": normalized.get("should_refuse"),
            "did_refuse": normalized.get("did_refuse"),
            "selected_failure_categories": normalized.get("selected_failure_categories") or [],
            "severity_override": normalized.get("severity_override"),
            "review_notes": normalized.get("review_notes") or normalized.get("notes"),
            "confidence": normalized.get("confidence"),
            "reviewer_time_seconds": normalized.get("reviewer_time_seconds"),
            "adjudication_status": normalized.get("adjudication_status") or "none",
            "sample": bool(normalized.get("sample")),
            "sample_notes": normalized.get("sample_notes"),
            "packet_metadata": normalized.get("packet_metadata"),
            "automated_failure_categories": automated.get("failure_categories", []),
            "automated_severity": automated.get("severity"),
            "automated_score": automated.get("overall_score"),
            "updated_by_import": datetime.now(UTC).isoformat(),
        }

    def _resolve_response(
        self,
        db: Session,
        normalized: dict[str, Any],
        experiment_id: uuid.UUID | None,
    ) -> ModelResponse:
        response_id = normalized.get("response_id")
        if response_id:
            response = db.get(ModelResponse, uuid.UUID(str(response_id)))
            if response is None:
                raise ReviewValidationError(f"Unknown response_id: {response_id}")
            return response
        evaluation_id = normalized.get("evaluation_id")
        if evaluation_id:
            evaluation = db.get(EvaluationResult, uuid.UUID(str(evaluation_id)))
            if evaluation is None:
                raise ReviewValidationError(f"Unknown evaluation_id: {evaluation_id}")
            return evaluation.model_response
        qa_id = normalized.get("qa_id")
        if not qa_id:
            raise ReviewValidationError("Review record needs response_id, evaluation_id, or qa_id")
        query = select(ModelResponse).join(QAExample).where(
            QAExample.metadata_json["qa_id"].as_string() == str(qa_id)
        )
        if experiment_id is not None:
            query = query.where(ModelResponse.experiment_id == experiment_id)
        responses = db.execute(query.order_by(ModelResponse.created_at.desc())).scalars().all()
        if not responses:
            raise ReviewValidationError(f"No response found for qa_id: {qa_id}")
        return responses[0]

    def _find_existing_review(
        self,
        db: Session,
        response_id: uuid.UUID,
        reviewer_label: str,
        source_record_id: str | None,
    ) -> HumanReview | None:
        reviews = (
            db.execute(select(HumanReview).where(HumanReview.model_response_id == response_id))
            .scalars()
            .all()
        )
        for review in reviews:
            metadata = self._review_metadata(review)
            if metadata.get("reviewer_label") != reviewer_label:
                continue
            if source_record_id is None or metadata.get("source_record_id") == source_record_id:
                return review
        return None

    def _summary_row(self, review: HumanReview) -> dict[str, Any]:
        metadata = self._review_metadata(review)
        calibration = self.calibration_for_review(review)
        row = {
            "review_id": str(review.id),
            "response_id": str(review.model_response_id),
            "reviewer_label": metadata.get("reviewer_label"),
            "reviewer_type": metadata.get("reviewer_type"),
            "review_status": metadata.get("review_status"),
            "answer_correctness": metadata.get("answer_correctness"),
            "groundedness": metadata.get("groundedness"),
            "citation_quality": metadata.get("citation_quality"),
            "refusal_safety": metadata.get("refusal_safety"),
            "should_refuse": metadata.get("should_refuse"),
            "did_refuse": metadata.get("did_refuse"),
            "automated_failure_categories": metadata.get("automated_failure_categories", []),
            "selected_failure_categories": metadata.get("selected_failure_categories", []),
            "severity_override": metadata.get("severity_override"),
            "sample": metadata.get("sample", False),
            "has_override": bool(
                set(metadata.get("automated_failure_categories") or [])
                != set(metadata.get("selected_failure_categories") or [])
                or (
                    metadata.get("severity_override")
                    and metadata.get("severity_override") != metadata.get("automated_severity")
                )
            ),
        }
        row.update(calibration)
        return row

    def _calibration_summary(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        jaccards = [
            row["category_jaccard"] for row in rows if row.get("category_jaccard") is not None
        ]
        refusal_matches = [
            row["refusal_decision_match"]
            for row in rows
            if row.get("refusal_decision_match") is not None
        ]
        return {
            "avg_category_jaccard": round(sum(jaccards) / len(jaccards), 3)
            if jaccards
            else None,
            "exact_category_match_count": sum(
                1 for row in rows if row.get("exact_category_match")
            ),
            "severity_match_count": sum(1 for row in rows if row.get("severity_match")),
            "refusal_decision_agreement_rate": round(
                sum(1 for item in refusal_matches if item) / len(refusal_matches), 3
            )
            if refusal_matches
            else None,
        }

    def _rubric_averages(self, reviews: list[HumanReview]) -> dict[str, float]:
        output: dict[str, float] = {}
        for key in ["answer_correctness", "groundedness", "citation_quality", "refusal_safety"]:
            scores = [
                self._review_metadata(review).get(key)
                for review in reviews
                if self._review_metadata(review).get(key) is not None
            ]
            if scores:
                output[key] = sum(float(score) for score in scores) / len(scores)
        return output

    @staticmethod
    def _validate_score(value: Any, field_name: str) -> None:
        if value is None:
            return
        if not isinstance(value, int) or value < 1 or value > 5:
            raise ReviewValidationError(f"{field_name} must be an integer from 1 to 5")

    @staticmethod
    def _score_label(value: int | None) -> str | None:
        if value is None:
            return None
        if value >= 4:
            return "correct"
        if value == 3:
            return "partially_correct"
        return "incorrect"

    @staticmethod
    def _groundedness_label(value: int | None) -> str | None:
        if value is None:
            return None
        if value >= 4:
            return "grounded"
        if value == 3:
            return "partially_grounded"
        return "unsupported"

    @staticmethod
    def _refusal_label(normalized: dict[str, Any]) -> str | None:
        should_refuse = normalized.get("should_refuse")
        did_refuse = normalized.get("did_refuse")
        if should_refuse is None or did_refuse is None:
            return "not_applicable"
        if should_refuse and did_refuse:
            return "correct_refusal"
        if should_refuse and not did_refuse:
            return "failed_refusal"
        if not should_refuse and did_refuse:
            return "over_refusal"
        return "not_applicable"

    @staticmethod
    def _experiment_payload(experiment: Experiment) -> dict[str, Any]:
        return {
            "id": str(experiment.id),
            "name": experiment.name,
            "status": experiment.status,
            "model_provider": experiment.model_provider,
            "model_name": experiment.model_name,
            "top_k": experiment.top_k,
            "metadata": experiment.metadata_json,
        }

    @staticmethod
    def _latest_evaluation(response: ModelResponse) -> EvaluationResult | None:
        if not response.evaluation_results:
            return None
        return sorted(
            response.evaluation_results,
            key=lambda item: item.created_at,
            reverse=True,
        )[0]

    def _automated_snapshot(self, response: ModelResponse) -> dict[str, Any]:
        evaluation = self._latest_evaluation(response)
        taxonomy = self._failure_taxonomy(evaluation)
        return {
            "failure_categories": taxonomy.get("failure_categories", []),
            "severity": taxonomy.get("severity"),
            "overall_score": evaluation.overall_score if evaluation else None,
        }

    @staticmethod
    def _automated_scores(evaluation: EvaluationResult | None) -> dict[str, Any]:
        if evaluation is None:
            return {}
        return {
            "correctness_score": evaluation.correctness_score,
            "groundedness_score": evaluation.groundedness_score,
            "citation_precision": evaluation.citation_precision,
            "citation_recall": evaluation.citation_recall,
            "retrieval_recall": evaluation.retrieval_recall,
            "refusal_score": evaluation.refusal_score,
            "overall_score": evaluation.overall_score,
        }

    @staticmethod
    def _failure_taxonomy(evaluation: EvaluationResult | None) -> dict[str, Any]:
        if evaluation is None:
            return {}
        metadata = evaluation.metadata_json or {}
        taxonomy = metadata.get("failure_taxonomy")
        if isinstance(taxonomy, dict):
            return taxonomy
        return {
            "legacy_failure_type": evaluation.failure_type,
            "failure_categories": failure_taxonomy.categories_for_legacy(evaluation.failure_type),
        }

    @staticmethod
    def _review_metadata(review: HumanReview) -> dict[str, Any]:
        return review.metadata_json or {}

    @staticmethod
    def _get_experiment(db: Session, experiment_id: uuid.UUID) -> Experiment:
        experiment = db.get(Experiment, experiment_id)
        if experiment is None:
            raise ValueError("Experiment not found")
        return experiment

    @staticmethod
    def _experiment_responses(db: Session, experiment_id: uuid.UUID) -> list[ModelResponse]:
        return (
            db.execute(
                select(ModelResponse)
                .where(ModelResponse.experiment_id == experiment_id)
                .order_by(ModelResponse.created_at.desc())
            )
            .scalars()
            .all()
        )


human_review_service = HumanReviewService()
