# Reproducibility

This page describes the MedEval v1 deterministic smoke workflow. It verifies the
local artifact loop:

```text
dataset -> seed -> deterministic runs -> evaluations -> rich failure diagnostics -> reports
```

The workflow uses the in-development MedEval v1 public healthcare seed dataset.
It uses deterministic local providers only and does not call OpenAI, Anthropic,
or any external model API.

## Prerequisites

- Docker Desktop or another Docker environment that supports `docker compose`.
- A backend virtual environment at `backend/.venv`.
- Backend package installed with development dependencies:

```bash
cd backend
python -m pip install -e ".[dev]"
```

The smoke script defaults to:

- `backend/.venv/bin/python`
- `backend/.venv/bin/medeval`

Override them if needed:

```bash
BACKEND_PYTHON=/path/to/python BACKEND_MEDEVAL=/path/to/medeval scripts/run_medeval_v1_smoke.sh
```

## Run The Smoke Workflow

From the repository root:

```bash
make medeval-v1-smoke
```

or:

```bash
scripts/run_medeval_v1_smoke.sh
```

The smoke workflow:

1. starts local Postgres with `docker compose up -d db`;
2. applies Alembic migrations;
3. validates `datasets/medeval-v1`;
4. prints dataset stats;
5. seeds MedEval v1 into the local database idempotently;
6. runs four deterministic configs:
   - baseline;
   - clean context;
   - metadata-assisted refusal control;
   - clean context refusal control;
7. exports baseline Markdown/JSON/CSV artifacts;
8. exports comparison Markdown/JSON/CSV artifacts;
9. runs the report artifact checker;
10. prints a success summary with experiment IDs and report paths.

## Check Existing Reports

To validate the currently checked-in report artifacts without regenerating them:

```bash
make medeval-v1-check-reports
```

or:

```bash
python3 scripts/check_medeval_v1_reports.py
```

The checker validates:

- required report files exist;
- Markdown reports include titles, disclaimers, deterministic/local wording,
  in-development wording, aggregate metrics, rich failure diagnostics, stage
  counts, severity counts, safety-relevant failure counts, and representative
  failure examples;
- JSON reports parse and include experiment metadata, aggregate metrics,
  compared experiments, deltas, failure counts, rich failure category counts,
  stage counts, severity counts, safety-relevant failure counts, and disclaimer
  or limitation text;
- CSV reports parse and include required columns for questions/answers,
  failure types, rich failure categories, severity, stage, safety-relevant
  flags, metrics, and comparison rows;
- obvious secret strings are absent.

The checker intentionally does not validate:

- exact metric values;
- clinical correctness;
- external model quality;
- real-world model leaderboard ranking;
- production readiness.

## Optional Manual Review Workflow

After a deterministic experiment run, you can export a curated pending review
packet, validate it, import completed reviews, check progress, and export
calibration summaries:

```bash
cd backend
medeval export-review-packet --experiment-id <experiment-id> --out ../reports/examples/medeval_v1_review_packet_50.pending.json --format json --limit 50 --strategy failure_priority
medeval validate-review-packet --path ../reports/examples/medeval_v1_review_packet_50.pending.json
medeval review-progress --experiment-id <experiment-id>
medeval import-review-packet --path ../reports/examples/medeval_v1_review_packet_50.pending.json --reviewer-label "mohit_manual_review"
medeval export-review-summary --experiment-id <experiment-id> --format markdown --out ../reports/medeval_v1_review_summary.md
```

You can still export the full review queue or import the sample fixture for
workflow testing:

```bash
medeval export-review-queue --experiment-id <experiment-id> --out ../reports/medeval_v1_review_queue.json
medeval import-reviews --path ../reports/examples/medeval_v1_reviews.sample.json --reviewer-label "sample_fixture_reviewer" --experiment-id <experiment-id>
```

Pending packets and the sample fixture are for workflow testing or future manual
review only. They are not real completed independent human review, clinician
review, clinical validation, or medical advice. See `docs/manual_review_packet.md`
and `docs/human_review.md`.

## Validate The Dataset Only

```bash
make medeval-v1-validate
```

This runs:

```bash
cd backend
medeval validate-dataset --path ../datasets/medeval-v1
medeval dataset-stats --path ../datasets/medeval-v1
```

## Limitations

MedEval v1 is still in development. The smoke workflow uses deterministic local
providers and heuristic rich failure diagnostics. The generated artifacts are
for reproducibility, debugging, and regression inspection. They are not clinical
validation, medical advice, a completed benchmark, production-use evidence,
external adoption evidence, or a real model leaderboard.
