import csv
import io
import uuid
from collections import Counter
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evaluation_result import EvaluationResult
from app.models.experiment import Experiment
from app.models.model_response import ModelResponse
from app.services.experiment_service import experiment_service

DISCLAIMER = (
    "This report is computed from the connected local database. Synthetic samples or "
    "in-development public healthcare seed datasets, deterministic providers, and "
    "heuristic evaluators are not validated benchmarks, clinical validation, medical "
    "advice, healthcare validation, or production-use evidence."
)


class ReportExportService:
    def build_report(self, db: Session, experiment_id: uuid.UUID) -> dict[str, Any]:
        experiment = db.get(Experiment, experiment_id)
        if experiment is None:
            raise ValueError("Experiment not found")
        results = experiment_service.aggregate_results(db, experiment_id)
        responses = self.response_rows(db, experiment_id)
        failures = [
            row
            for row in responses
            if row["failure_type"] not in {None, "none"} or row["hallucination_flag"]
        ]
        generated_at = datetime.now(UTC)
        claim_metrics = self._aggregate_claim_metrics(db, experiment_id)
        report = {
            "experiment": experiment,
            "results": results,
            "responses": responses,
            "failure_examples": failures[:10],
            "generated_at": generated_at,
            "disclaimer": DISCLAIMER,
            "metadata": {
                "report_type": "computed_markdown_json_csv",
                "failure_type_counts": dict(
                    Counter(row["failure_type"] or "unknown" for row in failures)
                ),
                "claim_metrics": claim_metrics,
                "limitations": [
                    "Synthetic samples and public healthcare seed datasets are in development.",
                    "The deterministic answer provider is not a real LLM.",
                    "The heuristic evaluator is not clinical validation.",
                ],
            },
        }
        report["markdown"] = self.markdown(report)
        return report

    def build_comparison_report(
        self, db: Session, experiment_ids: list[uuid.UUID]
    ) -> dict[str, Any]:
        if len(experiment_ids) < 2:
            raise ValueError("At least two experiment IDs are required for comparison")

        generated_at = datetime.now(UTC)
        summaries = []
        baseline_metrics: dict[str, float | None] | None = None
        for index, experiment_id in enumerate(experiment_ids):
            experiment = db.get(Experiment, experiment_id)
            if experiment is None:
                raise ValueError(f"Experiment not found: {experiment_id}")
            if experiment.status != "completed":
                raise ValueError(
                    f"Experiment {experiment_id} has status '{experiment.status}', "
                    "but compare-runs requires completed experiments"
                )
            aggregate = experiment_service.aggregate_results(db, experiment_id)
            metrics = self._comparison_metrics(aggregate)
            if index == 0:
                baseline_metrics = metrics
            summaries.append(
                {
                    "experiment_id": str(experiment.id),
                    "experiment_id_short": str(experiment.id)[:8],
                    "name": experiment.name,
                    "status": experiment.status,
                    "model_provider": experiment.model_provider,
                    "model_name": experiment.model_name,
                    "top_k": experiment.top_k,
                    "metadata": experiment.metadata_json,
                    "metrics": metrics,
                    "deltas_vs_baseline": self._metric_deltas(metrics, baseline_metrics or {}),
                    "failure_type_counts": aggregate.failure_type_counts,
                }
            )

        report = {
            "metadata": {
                "report_type": "deterministic_experiment_comparison",
                "generated_at": generated_at,
                "baseline_experiment_id": str(experiment_ids[0]),
                "experiment_count": len(summaries),
                "disclaimer": DISCLAIMER,
                "limitations": [
                    "This comparison is for deterministic local debugging and regression testing.",
                    "Metrics are computed from local database state and heuristic evaluators.",
                    "This is not clinical validation, medical advice, or a validated leaderboard.",
                ],
            },
            "experiments": summaries,
            "disclaimer": DISCLAIMER,
        }
        report["markdown"] = self.comparison_markdown(report)
        return report

    def response_rows(self, db: Session, experiment_id: uuid.UUID) -> list[dict[str, Any]]:
        responses = (
            db.execute(
                select(ModelResponse)
                .where(ModelResponse.experiment_id == experiment_id)
                .order_by(ModelResponse.created_at.desc())
            )
            .scalars()
            .all()
        )
        rows = []
        for response in responses:
            evaluation = self._latest_evaluation(response)
            metadata = evaluation.metadata_json if evaluation else {}
            failure_analysis = metadata.get("failure_analysis", {}) if metadata else {}
            claim_support = metadata.get("claim_support", {}) if metadata else {}
            rows.append(
                {
                    "response_id": str(response.id),
                    "qa_example_id": str(response.qa_example_id),
                    "question": response.qa_example.question,
                    "expected_answerability": response.qa_example.answerability,
                    "model_answerability": response.answerability,
                    "answer_text": response.answer_text,
                    "correctness_score": evaluation.correctness_score if evaluation else None,
                    "groundedness_score": evaluation.groundedness_score if evaluation else None,
                    "citation_precision": evaluation.citation_precision if evaluation else None,
                    "citation_recall": evaluation.citation_recall if evaluation else None,
                    "retrieval_precision": evaluation.retrieval_precision if evaluation else None,
                    "retrieval_recall": evaluation.retrieval_recall if evaluation else None,
                    "refusal_score": evaluation.refusal_score if evaluation else None,
                    "overall_score": evaluation.overall_score if evaluation else None,
                    "hallucination_flag": evaluation.hallucination_flag if evaluation else None,
                    "failure_type": evaluation.failure_type if evaluation else None,
                    "primary_failure_type": failure_analysis.get("primary_failure_type"),
                    "secondary_failure_types": failure_analysis.get("secondary_failure_types", []),
                    "failure_reason": failure_analysis.get("failure_reason"),
                    "retrieval_failure": failure_analysis.get("retrieval_failure"),
                    "generation_failure": failure_analysis.get("generation_failure"),
                    "claim_count": claim_support.get("claim_count"),
                    "claim_support_rate": claim_support.get("claim_support_rate"),
                    "unsupported_claim_rate": claim_support.get("unsupported_claim_rate"),
                    "created_at": response.created_at,
                }
            )
        return rows

    def markdown(self, report: dict[str, Any]) -> str:
        experiment: Experiment = report["experiment"]
        results = report["results"]
        metadata = report["metadata"]
        claim_metrics = metadata.get("claim_metrics", {})
        lines = [
            f"# MedEval Experiment Report: {experiment.name}",
            "",
            f"Generated: {report['generated_at'].isoformat()}",
            "",
            "## Disclaimer",
            "",
            report["disclaimer"],
            "",
            "## Experiment Config",
            "",
            f"- Status: {experiment.status}",
            f"- Dataset ID: {experiment.dataset_id}",
            f"- Model: {experiment.model_provider} / {experiment.model_name}",
            f"- Retrieval: {experiment.retrieval_strategy}, top_k={experiment.top_k}",
            f"- Embedding model: {experiment.embedding_model}",
            f"- Temperature: {experiment.temperature}",
            "",
            "## Aggregate Metrics",
            "",
            f"- Examples: {results.example_count}",
            f"- Avg correctness: {self._format_metric(results.avg_correctness)}",
            f"- Avg groundedness: {self._format_metric(results.avg_groundedness)}",
            f"- Citation precision: {self._format_metric(results.avg_citation_precision)}",
            f"- Citation recall: {self._format_metric(results.avg_citation_recall)}",
            f"- Retrieval recall: {self._format_metric(results.avg_retrieval_recall)}",
            f"- Refusal accuracy: {self._format_metric(results.refusal_accuracy)}",
            f"- Hallucination rate: {self._format_metric(results.hallucination_rate)}",
            "",
            "## Claim-Level Heuristics",
            "",
            "- Method: deterministic token-overlap heuristic; not benchmark-grade "
            "or clinically validated.",
            f"- Claim count: {claim_metrics.get('claim_count', 'n/a')}",
            f"- Claim support rate: {self._format_metric(claim_metrics.get('claim_support_rate'))}",
            "- Unsupported claim rate: "
            f"{self._format_metric(claim_metrics.get('unsupported_claim_rate'))}",
            "",
            "## Failure Counts",
            "",
        ]
        failure_counts = metadata.get("failure_type_counts", {})
        if failure_counts:
            lines.extend(
                f"- {failure_type}: {count}"
                for failure_type, count in failure_counts.items()
            )
        else:
            lines.append("- No failure rows found for this experiment.")
        lines.extend(["", "## Representative Failure Examples", ""])
        failures = report["failure_examples"]
        if failures:
            for failure in failures[:5]:
                lines.extend(
                    [
                        f"### {failure.get('failure_type') or 'flagged'}",
                        "",
                        f"Question: {failure['question']}",
                        "",
                        f"Failure reason: {failure.get('failure_reason') or 'n/a'}",
                        "",
                        f"Answer: {failure['answer_text']}",
                        "",
                    ]
                )
        else:
            lines.append("No representative failures available.")
        lines.extend(
            [
                "",
                "## Metric Definitions",
                "",
                "- Correctness: deterministic token-overlap approximation against the gold answer.",
                "- Groundedness: deterministic citation/claim support heuristic.",
                "- Retrieval recall: required evidence chunks retrieved divided by "
                "required evidence chunks.",
                "- Citation precision/recall: citation overlap with required or "
                "acceptable evidence links.",
                "",
                "## Reproducibility",
                "",
                "Use the experiment config, deterministic provider, sample data, "
                "and local database state to reproduce this run. No external model "
                "API is required for deterministic local runs.",
                "",
                "## Limitations",
                "",
                "- Synthetic samples and public healthcare seed datasets are for development only.",
                "- The deterministic provider is not a real LLM.",
                "- The heuristic evaluator is not clinical validation or healthcare validation.",
                "- This report does not claim real-world performance or adoption.",
            ]
        )
        return "\n".join(lines)

    def csv(self, rows: list[dict[str, Any]]) -> str:
        output = io.StringIO()
        fieldnames = [
            "response_id",
            "qa_example_id",
            "question",
            "expected_answerability",
            "model_answerability",
            "correctness_score",
            "groundedness_score",
            "citation_precision",
            "citation_recall",
            "retrieval_precision",
            "retrieval_recall",
            "refusal_score",
            "overall_score",
            "hallucination_flag",
            "failure_type",
            "primary_failure_type",
            "secondary_failure_types",
            "failure_reason",
            "retrieval_failure",
            "generation_failure",
            "claim_count",
            "claim_support_rate",
            "unsupported_claim_rate",
            "created_at",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            serializable = {
                key: ";".join(value) if isinstance(value, list) else value
                for key, value in row.items()
            }
            writer.writerow(serializable)
        return output.getvalue()

    def comparison_csv(self, report: dict[str, Any]) -> str:
        output = io.StringIO()
        fieldnames = [
            "experiment_id",
            "experiment_id_short",
            "name",
            "status",
            "model_provider",
            "model_name",
            "top_k",
            "examples",
            "avg_correctness",
            "avg_groundedness",
            "citation_precision",
            "citation_recall",
            "retrieval_precision",
            "retrieval_recall",
            "refusal_accuracy",
            "hallucination_rate",
            "avg_latency_ms",
            "total_estimated_cost",
            "correctness_delta",
            "groundedness_delta",
            "citation_recall_delta",
            "retrieval_recall_delta",
            "refusal_accuracy_delta",
            "hallucination_rate_delta",
            "failure_type_counts",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for experiment in report["experiments"]:
            metrics = experiment["metrics"]
            deltas = experiment["deltas_vs_baseline"]
            writer.writerow(
                {
                    "experiment_id": experiment["experiment_id"],
                    "experiment_id_short": experiment["experiment_id_short"],
                    "name": experiment["name"],
                    "status": experiment["status"],
                    "model_provider": experiment["model_provider"],
                    "model_name": experiment["model_name"],
                    "top_k": experiment["top_k"],
                    "examples": metrics["examples"],
                    "avg_correctness": metrics["avg_correctness"],
                    "avg_groundedness": metrics["avg_groundedness"],
                    "citation_precision": metrics["citation_precision"],
                    "citation_recall": metrics["citation_recall"],
                    "retrieval_precision": metrics["retrieval_precision"],
                    "retrieval_recall": metrics["retrieval_recall"],
                    "refusal_accuracy": metrics["refusal_accuracy"],
                    "hallucination_rate": metrics["hallucination_rate"],
                    "avg_latency_ms": metrics["avg_latency_ms"],
                    "total_estimated_cost": metrics["total_estimated_cost"],
                    "correctness_delta": deltas["avg_correctness_delta"],
                    "groundedness_delta": deltas["avg_groundedness_delta"],
                    "citation_recall_delta": deltas["citation_recall_delta"],
                    "retrieval_recall_delta": deltas["retrieval_recall_delta"],
                    "refusal_accuracy_delta": deltas["refusal_accuracy_delta"],
                    "hallucination_rate_delta": deltas["hallucination_rate_delta"],
                    "failure_type_counts": ";".join(
                        f"{key}:{value}"
                        for key, value in sorted(experiment["failure_type_counts"].items())
                    ),
                }
            )
        return output.getvalue()

    def comparison_markdown(self, report: dict[str, Any]) -> str:
        metadata = report["metadata"]
        lines = [
            "# MedEval v1 Deterministic Comparison Report",
            "",
            f"Generated: {metadata['generated_at'].isoformat()}",
            "",
            "## Disclaimer",
            "",
            report["disclaimer"],
            "",
            "This comparison is a deterministic local debugging/regression workflow for "
            "an in-development public healthcare seed dataset. It is not clinical "
            "validation, medical advice, or a validated leaderboard.",
            "",
            "## Compared Experiments",
            "",
            "| Experiment | ID | Status | Model | top_k | Examples |",
            "| --- | --- | --- | --- | ---: | ---: |",
        ]
        for experiment in report["experiments"]:
            metrics = experiment["metrics"]
            lines.append(
                f"| {experiment['name']} | {experiment['experiment_id_short']} | "
                f"{experiment['status']} | {experiment['model_name']} | "
                f"{experiment['top_k']} | {metrics['examples']} |"
            )

        lines.extend(
            [
                "",
                "## Aggregate Metrics",
                "",
                "| Experiment | Correctness | Groundedness | Citation Precision | "
                "Citation Recall | Retrieval Precision | Retrieval Recall | "
                "Refusal Accuracy | Hallucination Rate | Avg Latency | Cost |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for experiment in report["experiments"]:
            metrics = experiment["metrics"]
            lines.append(
                f"| {experiment['name']} | {self._format_metric(metrics['avg_correctness'])} | "
                f"{self._format_metric(metrics['avg_groundedness'])} | "
                f"{self._format_metric(metrics['citation_precision'])} | "
                f"{self._format_metric(metrics['citation_recall'])} | "
                f"{self._format_metric(metrics['retrieval_precision'])} | "
                f"{self._format_metric(metrics['retrieval_recall'])} | "
                f"{self._format_metric(metrics['refusal_accuracy'])} | "
                f"{self._format_metric(metrics['hallucination_rate'])} | "
                f"{self._format_metric(metrics['avg_latency_ms'])} | "
                f"{self._format_metric(metrics['total_estimated_cost'])} |"
            )

        lines.extend(
            [
                "",
                "## Deltas Vs Baseline",
                "",
                "| Experiment | Correctness Δ | Groundedness Δ | Citation Recall Δ | "
                "Retrieval Recall Δ | Refusal Accuracy Δ | Hallucination Rate Δ |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for experiment in report["experiments"]:
            deltas = experiment["deltas_vs_baseline"]
            lines.append(
                f"| {experiment['name']} | "
                f"{self._format_delta(deltas['avg_correctness_delta'])} | "
                f"{self._format_delta(deltas['avg_groundedness_delta'])} | "
                f"{self._format_delta(deltas['citation_recall_delta'])} | "
                f"{self._format_delta(deltas['retrieval_recall_delta'])} | "
                f"{self._format_delta(deltas['refusal_accuracy_delta'])} | "
                f"{self._format_delta(deltas['hallucination_rate_delta'])} |"
            )

        lines.extend(["", "## Failure Type Counts", ""])
        for experiment in report["experiments"]:
            lines.extend([f"### {experiment['name']}", ""])
            counts = experiment["failure_type_counts"]
            if counts:
                lines.extend(f"- {key}: {value}" for key, value in sorted(counts.items()))
            else:
                lines.append("- No failure counts available.")
            lines.append("")

        lines.extend(
            [
                "## Notes And Limitations",
                "",
                "- Deterministic local comparisons are useful for pipeline debugging and "
                "regression testing.",
                "- Refusal-aware variants may use QA metadata as a deterministic control, "
                "not as a real model capability.",
                "- Clean-context variants strip frontmatter and source metadata before "
                "deterministic answer generation.",
                "- These reports do not claim real-world performance, clinical validation, "
                "production readiness, or external adoption.",
            ]
        )
        return "\n".join(lines)

    @staticmethod
    def _latest_evaluation(response: ModelResponse) -> EvaluationResult | None:
        if not response.evaluation_results:
            return None
        return sorted(
            response.evaluation_results,
            key=lambda item: item.created_at,
            reverse=True,
        )[0]

    def _aggregate_claim_metrics(self, db: Session, experiment_id: uuid.UUID) -> dict[str, Any]:
        evaluations = (
            db.execute(
                select(EvaluationResult)
                .join(ModelResponse)
                .where(ModelResponse.experiment_id == experiment_id)
            )
            .scalars()
            .all()
        )
        support_rates = []
        unsupported_rates = []
        claim_count = 0
        for evaluation in evaluations:
            claim_support = evaluation.metadata_json.get("claim_support", {})
            claim_count += int(claim_support.get("claim_count") or 0)
            if claim_support.get("claim_support_rate") is not None:
                support_rates.append(float(claim_support["claim_support_rate"]))
            if claim_support.get("unsupported_claim_rate") is not None:
                unsupported_rates.append(float(claim_support["unsupported_claim_rate"]))
        return {
            "claim_count": claim_count,
            "claim_support_rate": self._avg(support_rates),
            "unsupported_claim_rate": self._avg(unsupported_rates),
        }

    @staticmethod
    def _avg(values: list[float]) -> float | None:
        if not values:
            return None
        return sum(values) / len(values)

    @staticmethod
    def _format_metric(value: object) -> str:
        if value is None:
            return "n/a"
        if isinstance(value, int | float):
            return f"{value:.3f}"
        return str(value)

    @staticmethod
    def _format_delta(value: object) -> str:
        if value is None:
            return "n/a"
        if isinstance(value, int | float):
            return f"{value:+.3f}"
        return str(value)

    @staticmethod
    def _comparison_metrics(results) -> dict[str, float | int | None]:
        return {
            "examples": results.example_count,
            "avg_correctness": results.avg_correctness,
            "avg_groundedness": results.avg_groundedness,
            "citation_precision": results.avg_citation_precision,
            "citation_recall": results.avg_citation_recall,
            "retrieval_precision": results.avg_retrieval_precision,
            "retrieval_recall": results.avg_retrieval_recall,
            "refusal_accuracy": results.refusal_accuracy,
            "hallucination_rate": results.hallucination_rate,
            "avg_latency_ms": results.avg_latency_ms,
            "total_estimated_cost": results.total_estimated_cost,
        }

    @staticmethod
    def _metric_deltas(
        metrics: dict[str, float | int | None],
        baseline: dict[str, float | int | None],
    ) -> dict[str, float | None]:
        pairs = {
            "avg_correctness_delta": "avg_correctness",
            "avg_groundedness_delta": "avg_groundedness",
            "citation_recall_delta": "citation_recall",
            "retrieval_recall_delta": "retrieval_recall",
            "refusal_accuracy_delta": "refusal_accuracy",
            "hallucination_rate_delta": "hallucination_rate",
        }
        deltas: dict[str, float | None] = {}
        for output_key, metric_key in pairs.items():
            value = metrics.get(metric_key)
            baseline_value = baseline.get(metric_key)
            if value is None or baseline_value is None:
                deltas[output_key] = None
            else:
                deltas[output_key] = float(value) - float(baseline_value)
        return deltas


report_export_service = ReportExportService()
