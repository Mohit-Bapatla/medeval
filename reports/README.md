# Reports

This directory contains checked-in MedEval v1 deterministic report artifacts and
manual-review calibration artifacts. Do not commit fabricated benchmark results,
secrets, PHI, private medical records, private student data, or sensitive local
outputs.

## Deterministic Report Artifacts

These files are generated from local Postgres-backed deterministic runs over
the in-development MedEval v1 public healthcare seed dataset:

| File | Purpose |
| --- | --- |
| `medeval_v1_seed_report.md` | Baseline Markdown report |
| `medeval_v1_seed_report.json` | Baseline structured report payload |
| `medeval_v1_seed_results.csv` | Baseline per-response results |
| `medeval_v1_comparison_report.md` | Four-config comparison report |
| `medeval_v1_comparison_report.json` | Structured comparison payload |
| `medeval_v1_comparison_results.csv` | CSV comparison summary |

The current MedEval v1 dataset contains 25 public healthcare documents and 230
evidence-linked QA examples. The comparison report includes four deterministic
configs: baseline, clean context, metadata-assisted refusal control, and clean
context refusal control.

The artifacts include aggregate metrics, legacy `failure_type` counts, rich
failure category counts, failure stage counts, severity counts, safety-relevant
failure counts, and representative failure diagnostics.

## Manual-Review Calibration Artifacts

These files support the manual self-review calibration workflow:

| File | Purpose |
| --- | --- |
| `medeval_v1_manual_review_summary.md` | Human-readable calibration summary |
| `medeval_v1_manual_review_summary.json` | Structured calibration summary |
| `medeval_v1_manual_review_summary.csv` | Per-review calibration rows |
| `examples/medeval_v1_review_packet_50.pending.json` | Blank pending packet template |
| `examples/medeval_v1_review_packet_50.pending.md` | Markdown worksheet for the pending packet |
| `examples/medeval_v1_review_packet_50.completed.json` | Completed self-review packet |
| `examples/medeval_v1_reviews.sample.json` | Tiny sample fixture for workflow tests |

The completed packet contains 50 manual self-review calibration labels for
high-priority deterministic baseline failures. These labels are not clinician
review, clinical validation, medical advice, production-use evidence, external
adoption evidence, or human-validated benchmark certification.

## Artifact Sizes

As of the current MedEval v1 packaging pass, the largest checked-in artifacts
are the baseline JSON report and review packets. They are intentionally small
enough for repository review:

```bash
ls -lh reports/ reports/examples/
```

## Regenerate Deterministic Reports

The shortest path from the repository root is:

```bash
make medeval-v1-smoke
```

To validate checked-in artifacts without regenerating them:

```bash
make medeval-v1-check-reports
```

Manual reproduction:

```bash
docker compose up -d db
cd backend
python -m alembic upgrade head
medeval validate-dataset --path ../datasets/medeval-v1
medeval dataset-stats --path ../datasets/medeval-v1
medeval seed-dataset --path ../datasets/medeval-v1 --dataset-name "MedEval v1 Public Healthcare Seed"
medeval run-experiment --config ../configs/experiments/medeval_v1_deterministic.yaml
medeval run-experiment --config ../configs/experiments/medeval_v1_deterministic_clean_context.yaml
medeval run-experiment --config ../configs/experiments/medeval_v1_deterministic_refusal_aware.yaml
medeval run-experiment --config ../configs/experiments/medeval_v1_deterministic_top5_clean_refusal.yaml
```

Use the printed experiment IDs:

```bash
medeval export-report --experiment-id <baseline-id> --format markdown --out ../reports/medeval_v1_seed_report.md
medeval export-report --experiment-id <baseline-id> --format json --out ../reports/medeval_v1_seed_report.json
medeval export-results --experiment-id <baseline-id> --format csv --out ../reports/medeval_v1_seed_results.csv
medeval compare-runs \
  --experiment-id <baseline-id> \
  --experiment-id <clean-context-id> \
  --experiment-id <refusal-aware-id> \
  --experiment-id <clean-refusal-id> \
  --format markdown \
  --out ../reports/medeval_v1_comparison_report.md

medeval compare-runs \
  --experiment-id <baseline-id> \
  --experiment-id <clean-context-id> \
  --experiment-id <refusal-aware-id> \
  --experiment-id <clean-refusal-id> \
  --format json \
  --out ../reports/medeval_v1_comparison_report.json

medeval compare-runs \
  --experiment-id <baseline-id> \
  --experiment-id <clean-context-id> \
  --experiment-id <refusal-aware-id> \
  --experiment-id <clean-refusal-id> \
  --format csv \
  --out ../reports/medeval_v1_comparison_results.csv
```

## Regenerate Review Artifacts

```bash
cd backend
medeval export-review-packet \
  --experiment-id <experiment-id> \
  --out ../reports/examples/medeval_v1_review_packet_50.pending.json \
  --format json \
  --limit 50 \
  --strategy failure_priority

medeval export-review-packet \
  --experiment-id <experiment-id> \
  --out ../reports/examples/medeval_v1_review_packet_50.pending.md \
  --format markdown \
  --limit 50 \
  --strategy failure_priority
medeval validate-review-packet --path ../reports/examples/medeval_v1_review_packet_50.pending.json
medeval import-review-packet --path ../reports/examples/medeval_v1_review_packet_50.completed.json --reviewer-label "mohit_manual_review"
medeval review-progress --experiment-id <experiment-id>
medeval export-review-summary --experiment-id <experiment-id> --format markdown --out ../reports/medeval_v1_manual_review_summary.md
medeval export-review-summary --experiment-id <experiment-id> --format json --out ../reports/medeval_v1_manual_review_summary.json
medeval export-review-summary --experiment-id <experiment-id> --format csv --out ../reports/medeval_v1_manual_review_summary.csv
```

## What Not To Infer

These reports do not claim:

- clinical validation;
- clinician review;
- medical advice;
- production readiness;
- external adoption;
- state-of-the-art model performance;
- a validated public healthcare leaderboard.

They are deterministic local artifacts for benchmark development, debugging,
regression testing, report reproducibility, and manual calibration.

See [docs/benchmark_report_v1.md](../docs/benchmark_report_v1.md) and
[docs/reproducibility.md](../docs/reproducibility.md) for the broader workflow.
