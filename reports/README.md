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

These artifacts were generated from local Postgres-backed deterministic runs
over 14 public healthcare documents and 92 evidence-linked QA examples. The
comparison report includes four deterministic configs: baseline, clean-context,
metadata-assisted refusal control, and clean-context refusal control.

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
