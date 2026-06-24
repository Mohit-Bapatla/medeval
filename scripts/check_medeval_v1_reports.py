#!/usr/bin/env python3
"""Validate MedEval v1 deterministic report artifacts.

This checker validates report structure, qualitative labels, rich failure
diagnostic fields, and obvious secret leaks. It intentionally does not validate
exact metric values.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORTS_DIR = REPO_ROOT / "reports"

SEED_REPORT_MD = "medeval_v1_seed_report.md"
SEED_REPORT_JSON = "medeval_v1_seed_report.json"
SEED_RESULTS_CSV = "medeval_v1_seed_results.csv"
COMPARISON_REPORT_MD = "medeval_v1_comparison_report.md"
COMPARISON_REPORT_JSON = "medeval_v1_comparison_report.json"
COMPARISON_RESULTS_CSV = "medeval_v1_comparison_results.csv"

SECRET_PATTERNS = [
    re.compile(r"OPENAI_API_KEY", re.IGNORECASE),
    re.compile(r"ANTHROPIC_API_KEY", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}"),
    re.compile(r"DATABASE_URL\s*=\s*\S+:\S+@", re.IGNORECASE),
    re.compile(r"\.env\b", re.IGNORECASE),
]


class ReportCheckError(Exception):
    """Raised when a report artifact fails validation."""


def validate_reports(reports_dir: Path = DEFAULT_REPORTS_DIR) -> list[str]:
    messages: list[str] = []
    reports_dir = reports_dir.resolve()
    _check_seed_markdown(reports_dir / SEED_REPORT_MD, messages)
    _check_comparison_markdown(reports_dir / COMPARISON_REPORT_MD, messages)
    _check_seed_json(reports_dir / SEED_REPORT_JSON, messages)
    _check_comparison_json(reports_dir / COMPARISON_REPORT_JSON, messages)
    _check_seed_csv(reports_dir / SEED_RESULTS_CSV, messages)
    _check_comparison_csv(reports_dir / COMPARISON_RESULTS_CSV, messages)
    return messages


def _check_seed_markdown(path: Path, messages: list[str]) -> None:
    text = _read_text(path)
    _check_no_secrets(path, text)
    checks = {
        "title": "# MedEval Experiment Report",
        "disclaimer": "## Disclaimer",
        "deterministic wording": "deterministic",
        "local wording": "local",
        "in-development wording": "in-development",
        "not clinically validated wording": "clinical validation",
        "not medical advice wording": "medical advice",
        "aggregate metrics section": "## Aggregate Metrics",
        "rich diagnostics section": "## Rich Failure Diagnostics",
        "severity counts": "### Severity",
        "stage counts": "### Failure Stages",
        "safety-relevant count": "Safety-relevant failures",
        "representative failures": "## Representative Failure Examples",
    }
    _require_markdown_terms(path, text, checks)
    messages.append(f"PASS {path.name}: markdown structure and safety checks")


def _check_comparison_markdown(path: Path, messages: list[str]) -> None:
    text = _read_text(path)
    _check_no_secrets(path, text)
    checks = {
        "title": "# MedEval v1 Deterministic Comparison Report",
        "disclaimer": "## Disclaimer",
        "compared experiments section": "## Compared Experiments",
        "aggregate metric comparison": "## Aggregate Metrics",
        "delta vs baseline section": "## Deltas Vs Baseline",
        "rich diagnostics section": "## Rich Failure Diagnostics",
        "deterministic wording": "deterministic",
        "in-development wording": "in-development",
    }
    _require_markdown_terms(path, text, checks)
    lowered = text.lower()
    if "metadata-assisted" not in lowered and "oracle/control" not in lowered:
        raise ReportCheckError(
            f"{path}: expected metadata-assisted refusal control wording"
        )
    messages.append(f"PASS {path.name}: markdown structure and safety checks")


def _check_seed_json(path: Path, messages: list[str]) -> None:
    payload = _read_json(path)
    _check_no_secrets(path, path.read_text(encoding="utf-8"))
    experiment = _require_dict(payload, "experiment", path)
    results = _require_dict(payload, "results", path)
    metadata = _require_dict(payload, "metadata", path)
    if not (experiment.get("id") or payload.get("experiment_id")):
        raise ReportCheckError(f"{path}: missing experiment id")
    if not experiment.get("name"):
        raise ReportCheckError(f"{path}: missing experiment/config metadata")
    example_count = _number(results.get("example_count"))
    if example_count < 90:
        raise ReportCheckError(f"{path}: expected example_count >= 90, got {example_count}")
    for key in [
        "failure_type_counts",
        "rich_failure_category_counts",
        "failure_stage_counts",
        "failure_severity_counts",
        "safety_relevant_failure_count",
    ]:
        if key not in metadata:
            raise ReportCheckError(f"{path}: missing metadata.{key}")
    failures = payload.get("failure_examples")
    if not isinstance(failures, list) or not failures:
        raise ReportCheckError(f"{path}: missing representative failure examples")
    if "disclaimer" not in payload and "limitations" not in metadata:
        raise ReportCheckError(f"{path}: missing disclaimer or limitations")
    messages.append(f"PASS {path.name}: JSON structure checks")


def _check_comparison_json(path: Path, messages: list[str]) -> None:
    payload = _read_json(path)
    _check_no_secrets(path, path.read_text(encoding="utf-8"))
    experiments = payload.get("experiments")
    if not isinstance(experiments, list) or len(experiments) < 2:
        raise ReportCheckError(f"{path}: expected at least two compared experiments")
    for index, experiment in enumerate(experiments):
        if not isinstance(experiment, dict):
            raise ReportCheckError(f"{path}: experiment {index} is not an object")
        for key in ["experiment_id", "name", "status", "metrics"]:
            if key not in experiment:
                raise ReportCheckError(f"{path}: experiment {index} missing {key}")
        metrics = _require_dict(experiment, "metrics", path)
        if _number(metrics.get("examples")) < 90:
            raise ReportCheckError(f"{path}: experiment {index} expected examples >= 90")
        if "deltas_vs_baseline" not in experiment:
            raise ReportCheckError(f"{path}: experiment {index} missing deltas_vs_baseline")
        for key in [
            "rich_failure_category_counts",
            "failure_stage_counts",
            "failure_severity_counts",
            "safety_relevant_failure_count",
        ]:
            if key not in experiment:
                raise ReportCheckError(f"{path}: experiment {index} missing {key}")
    metadata = _require_dict(payload, "metadata", path)
    if "disclaimer" not in payload and "limitations" not in metadata:
        raise ReportCheckError(f"{path}: missing disclaimer or limitations")
    messages.append(f"PASS {path.name}: JSON structure checks")


def _check_seed_csv(path: Path, messages: list[str]) -> None:
    rows, columns, text = _read_csv(path)
    _check_no_secrets(path, text)
    if len(rows) < 90:
        raise ReportCheckError(f"{path}: expected at least 90 rows, got {len(rows)}")
    _require_any_column(path, columns, ["question", "qa_id"])
    _require_any_column(path, columns, ["answer_text", "answer", "response"])
    _require_columns(
        path,
        columns,
        [
            "failure_type",
            "failure_severity",
            "failure_stage",
            "safety_relevant_failure",
        ],
    )
    _require_any_column(path, columns, ["primary_failure_category", "failure_categories"])
    messages.append(f"PASS {path.name}: CSV structure and safety checks")


def _check_comparison_csv(path: Path, messages: list[str]) -> None:
    rows, columns, text = _read_csv(path)
    _check_no_secrets(path, text)
    if len(rows) < 2:
        raise ReportCheckError(f"{path}: expected at least two rows, got {len(rows)}")
    _require_columns(
        path,
        columns,
        [
            "experiment_id",
            "avg_correctness",
            "avg_groundedness",
            "citation_recall",
            "retrieval_recall",
            "refusal_accuracy",
            "hallucination_rate",
        ],
    )
    _require_any_column(path, columns, ["experiment_name", "name"])
    _require_any_column(path, columns, ["example_count", "examples"])
    _require_any_column(
        path,
        columns,
        ["rich_failure_category_counts", "failure_category_counts"],
    )
    messages.append(f"PASS {path.name}: CSV structure and safety checks")


def _read_text(path: Path) -> str:
    if not path.exists():
        raise ReportCheckError(f"Missing required report artifact: {path}")
    return path.read_text(encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    text = _read_text(path)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ReportCheckError(f"{path}: invalid JSON ({exc})") from exc
    if not isinstance(payload, dict):
        raise ReportCheckError(f"{path}: expected JSON object")
    return payload


def _read_csv(path: Path) -> tuple[list[dict[str, str]], set[str], str]:
    text = _read_text(path)
    reader = csv.DictReader(text.splitlines())
    rows = list(reader)
    columns = set(reader.fieldnames or [])
    if not columns:
        raise ReportCheckError(f"{path}: missing CSV header")
    return rows, columns, text


def _check_no_secrets(path: Path, text: str) -> None:
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            raise ReportCheckError(
                f"{path}: possible secret or local environment reference matched "
                f"{pattern.pattern!r}"
            )


def _require_markdown_terms(path: Path, text: str, checks: dict[str, str]) -> None:
    lowered = text.lower()
    for label, term in checks.items():
        if term.lower() not in lowered:
            raise ReportCheckError(f"{path}: missing {label} ({term!r})")


def _require_dict(payload: dict[str, Any], key: str, path: Path) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ReportCheckError(f"{path}: missing object {key}")
    return value


def _number(value: Any) -> float:
    if isinstance(value, int | float):
        return float(value)
    return 0.0


def _require_columns(path: Path, columns: set[str], required: list[str]) -> None:
    missing = [column for column in required if column not in columns]
    if missing:
        raise ReportCheckError(f"{path}: missing required columns: {', '.join(missing)}")


def _require_any_column(path: Path, columns: set[str], alternatives: list[str]) -> None:
    if not any(column in columns for column in alternatives):
        raise ReportCheckError(
            f"{path}: missing one of required columns: {', '.join(alternatives)}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate MedEval v1 deterministic report artifacts."
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=DEFAULT_REPORTS_DIR,
        help="Directory containing MedEval v1 report artifacts.",
    )
    args = parser.parse_args(argv)

    try:
        messages = validate_reports(args.reports_dir)
    except ReportCheckError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1

    for message in messages:
        print(message)
    print(
        "PASS all MedEval v1 deterministic report artifact checks completed "
        "without exact metric assertions."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
