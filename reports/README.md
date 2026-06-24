# Reports

Generated reports can be written here during local development. Do not commit
fabricated benchmark results, secrets, PHI, private medical records, private
student data, or reports containing sensitive data.

## Current Deterministic Seed Artifacts

This directory includes small, clearly labeled deterministic local report
artifacts for the in-development MedEval v1 public healthcare seed dataset:

- `medeval_v1_seed_report.md`
- `medeval_v1_seed_report.json`
- `medeval_v1_seed_results.csv`
- `medeval_v1_comparison_report.md`
- `medeval_v1_comparison_report.json`
- `medeval_v1_comparison_results.csv`

These artifacts are generated from local Postgres-backed deterministic runs.
After Batch 11, the current MedEval v1 dataset contains 25 public healthcare
documents and 230 evidence-linked QA examples. The comparison report includes
four deterministic configs: baseline, clean-context, metadata-assisted refusal
control, and clean-context refusal control.

The reports include aggregate metrics, legacy `failure_type` counts, rich
failure category counts, failure stage counts, severity counts, safety-relevant
failure counts, and representative failure diagnostics.

These are deterministic local report artifacts for debugging and regression
testing. They are not a validated benchmark, clinical validation, medical
advice, healthcare validation, production-use evidence, a real model
leaderboard, or an external adoption claim.

## Reproduce The Artifacts

The shortest path is:

```bash
make medeval-v1-smoke
```

To validate the currently checked-in artifacts without regenerating them:

```bash
make medeval-v1-check-reports
```

See `docs/reproducibility.md` for details.

From the repository root:

```bash
docker compose up -d db
```

From `backend/`:

```bash
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
medeval compare-runs --experiment-id <baseline-id> --experiment-id <clean-context-id> --experiment-id <refusal-aware-id> --experiment-id <clean-refusal-id> --format markdown --out ../reports/medeval_v1_comparison_report.md
medeval compare-runs --experiment-id <baseline-id> --experiment-id <clean-context-id> --experiment-id <refusal-aware-id> --experiment-id <clean-refusal-id> --format json --out ../reports/medeval_v1_comparison_report.json
medeval compare-runs --experiment-id <baseline-id> --experiment-id <clean-context-id> --experiment-id <refusal-aware-id> --experiment-id <clean-refusal-id> --format csv --out ../reports/medeval_v1_comparison_results.csv
```

## Manual Review Artifacts

`reports/examples/medeval_v1_reviews.sample.json` is a tiny sample fixture for
testing the MedEval v1 manual review import workflow. It is marked
`sample: true` and is not real independent human review, clinician review,
clinical validation, medical advice, or benchmark validation.

`reports/examples/medeval_v1_review_packet_50.pending.json` and the matching
Markdown worksheet, when present, are pending manual review packets. They contain
blank review fields and are not completed human review. Do not cite them as
human-reviewed outputs until a reviewer fills them out, validates them, and
imports the completed records.

Generate review artifacts on demand:

```bash
cd backend
medeval export-review-packet --experiment-id <experiment-id> --out ../reports/examples/medeval_v1_review_packet_50.pending.json --format json --limit 50 --strategy failure_priority
medeval export-review-packet --experiment-id <experiment-id> --out ../reports/examples/medeval_v1_review_packet_50.pending.md --format markdown --limit 50 --strategy failure_priority
medeval validate-review-packet --path ../reports/examples/medeval_v1_review_packet_50.pending.json
medeval review-progress --experiment-id <experiment-id>
medeval import-review-packet --path ../reports/examples/medeval_v1_review_packet_50.pending.json --reviewer-label "mohit_manual_review"
medeval export-review-queue --experiment-id <experiment-id> --out ../reports/medeval_v1_review_queue.json
medeval import-reviews --path ../reports/examples/medeval_v1_reviews.sample.json --reviewer-label "sample_fixture_reviewer" --experiment-id <experiment-id>
medeval export-review-summary --experiment-id <experiment-id> --format markdown --out ../reports/medeval_v1_review_summary.md
medeval export-review-summary --experiment-id <experiment-id> --format json --out ../reports/medeval_v1_review_summary.json
medeval export-review-summary --experiment-id <experiment-id> --format csv --out ../reports/medeval_v1_review_summary.csv
```

See `docs/manual_review_packet.md` for the rubric and packet workflow.
