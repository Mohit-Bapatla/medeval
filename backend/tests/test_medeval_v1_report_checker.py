import importlib.util
import json
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CHECKER_PATH = REPO_ROOT / "scripts" / "check_medeval_v1_reports.py"
SMOKE_SCRIPT_PATH = REPO_ROOT / "scripts" / "run_medeval_v1_smoke.sh"

spec = importlib.util.spec_from_file_location("check_medeval_v1_reports", CHECKER_PATH)
assert spec is not None and spec.loader is not None
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def test_report_checker_passes_on_committed_artifacts() -> None:
    messages = checker.validate_reports(REPO_ROOT / "reports")

    assert len(messages) == 6
    assert any("medeval_v1_seed_report.md" in message for message in messages)


def test_report_checker_fails_on_missing_required_artifact(tmp_path: Path) -> None:
    _write_valid_report_fixture(tmp_path)
    (tmp_path / "medeval_v1_seed_report.md").unlink()

    with pytest.raises(checker.ReportCheckError, match="Missing required report artifact"):
        checker.validate_reports(tmp_path)


def test_report_checker_fails_on_missing_disclaimer(tmp_path: Path) -> None:
    _write_valid_report_fixture(tmp_path)
    report_path = tmp_path / "medeval_v1_seed_report.md"
    report_path.write_text(
        "# MedEval Experiment Report\n\n## Aggregate Metrics\n",
        encoding="utf-8",
    )

    with pytest.raises(checker.ReportCheckError, match="missing disclaimer"):
        checker.validate_reports(tmp_path)


def test_report_checker_catches_obvious_secret_strings(tmp_path: Path) -> None:
    _write_valid_report_fixture(tmp_path)
    report_path = tmp_path / "medeval_v1_seed_report.md"
    with report_path.open("a", encoding="utf-8") as handle:
        handle.write("\nOPENAI_API_KEY=sk-testsecret123456\n")

    with pytest.raises(checker.ReportCheckError, match="possible secret"):
        checker.validate_reports(tmp_path)


def test_smoke_script_is_executable() -> None:
    assert SMOKE_SCRIPT_PATH.exists()
    assert os.access(SMOKE_SCRIPT_PATH, os.X_OK)


def _write_valid_report_fixture(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "medeval_v1_seed_report.md").write_text(
        "\n".join(
            [
                "# MedEval Experiment Report: fixture",
                "## Disclaimer",
                "local deterministic in-development not clinical validation medical advice",
                "## Aggregate Metrics",
                "## Rich Failure Diagnostics",
                "### Failure Stages",
                "### Severity",
                "- Safety-relevant failures: 1",
                "## Representative Failure Examples",
            ]
        ),
        encoding="utf-8",
    )
    (path / "medeval_v1_comparison_report.md").write_text(
        "\n".join(
            [
                "# MedEval v1 Deterministic Comparison Report",
                "## Disclaimer",
                "local deterministic in-development metadata-assisted refusal oracle/control",
                "## Compared Experiments",
                "## Aggregate Metrics",
                "## Deltas Vs Baseline",
                "## Rich Failure Diagnostics",
            ]
        ),
        encoding="utf-8",
    )
    (path / "medeval_v1_seed_report.json").write_text(
        json.dumps(
            {
                "experiment": {"id": "exp-1", "name": "Fixture baseline"},
                "results": {"example_count": 90},
                "metadata": {
                    "failure_type_counts": {"wrong_answer": 1},
                    "rich_failure_category_counts": {"bad_synthesis": 1},
                    "failure_stage_counts": {"synthesis": 1},
                    "failure_severity_counts": {"high": 1},
                    "safety_relevant_failure_count": 1,
                    "limitations": ["not clinical validation"],
                },
                "failure_examples": [{"question": "Fixture?", "answer_text": "Fixture."}],
                "disclaimer": "not a validated benchmark",
            }
        ),
        encoding="utf-8",
    )
    (path / "medeval_v1_comparison_report.json").write_text(
        json.dumps(
            {
                "metadata": {
                    "limitations": ["deterministic local only"],
                    "disclaimer": "not clinical validation",
                },
                "experiments": [
                    _comparison_experiment("exp-1", "Baseline"),
                    _comparison_experiment("exp-2", "Variant"),
                ],
                "disclaimer": "not a validated benchmark",
            }
        ),
        encoding="utf-8",
    )
    (path / "medeval_v1_seed_results.csv").write_text(
        "\n".join(
            [
                "question,answer_text,failure_type,primary_failure_category,"
                "failure_severity,failure_stage,safety_relevant_failure",
                *[
                    f"Question {index},Answer {index},wrong_answer,bad_synthesis,"
                    "high,synthesis,True"
                    for index in range(90)
                ],
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (path / "medeval_v1_comparison_results.csv").write_text(
        "\n".join(
            [
                "experiment_id,name,examples,avg_correctness,avg_groundedness,"
                "citation_recall,retrieval_recall,refusal_accuracy,hallucination_rate,"
                "rich_failure_category_counts",
                "exp-1,Baseline,90,0.1,0.2,0.3,0.4,0.5,0.6,bad_synthesis:1",
                "exp-2,Variant,90,0.2,0.3,0.4,0.5,0.6,0.7,bad_synthesis:1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _comparison_experiment(experiment_id: str, name: str) -> dict:
    return {
        "experiment_id": experiment_id,
        "name": name,
        "status": "completed",
        "metrics": {"examples": 90},
        "deltas_vs_baseline": {"avg_correctness_delta": 0.0},
        "rich_failure_category_counts": {"bad_synthesis": 1},
        "failure_stage_counts": {"synthesis": 1},
        "failure_severity_counts": {"high": 1},
        "safety_relevant_failure_count": 1,
    }
