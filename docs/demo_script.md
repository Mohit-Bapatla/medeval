# MedEval v1 Demo Script

This walkthrough takes 5-10 minutes on a machine with Docker, Python, and Node
installed. It uses deterministic local providers only. No OpenAI, Anthropic, or
external model API keys are required.

## 1. Start The Database

```bash
docker compose up -d db
```

## 2. Install The Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
```

What this demonstrates: local Postgres + pgvector storage, Alembic migrations,
and a reproducible backend environment.

## 3. Validate The Public Dataset

```bash
medeval validate-dataset --path ../datasets/medeval-v1
medeval dataset-stats --path ../datasets/medeval-v1
```

What this demonstrates: MedEval v1 currently has 25 public healthcare source
documents and 230 exact-evidence QA examples, split across eval, hard, and
refusal files.

## 4. Seed MedEval v1

```bash
medeval seed-dataset \
  --path ../datasets/medeval-v1 \
  --dataset-name "MedEval v1 Public Healthcare Seed"
```

What this demonstrates: documents, chunks, deterministic embeddings, QA
examples, and evidence links can be loaded into the local database
idempotently.

## 5. Run A Deterministic Baseline

```bash
medeval run-experiment \
  --config ../configs/experiments/medeval_v1_deterministic.yaml
```

Copy the printed experiment ID. The deterministic provider is for reproducible
pipeline testing, not real model leaderboard claims.

## 6. Export A Report

```bash
medeval export-report \
  --experiment-id <experiment-id> \
  --format markdown \
  --out ../reports/medeval_v1_seed_report.md

medeval export-results \
  --experiment-id <experiment-id> \
  --format csv \
  --out ../reports/medeval_v1_seed_results.csv
```

What this demonstrates: report generation, per-response CSV export, aggregate
metrics, failure diagnostics, and reproducible artifacts.

## 7. Compare Configs

Run additional deterministic configs:

```bash
medeval run-experiment --config ../configs/experiments/medeval_v1_deterministic_clean_context.yaml
medeval run-experiment --config ../configs/experiments/medeval_v1_deterministic_refusal_aware.yaml
medeval run-experiment --config ../configs/experiments/medeval_v1_deterministic_top5_clean_refusal.yaml
```

Then compare them:

```bash
medeval compare-runs \
  --experiment-id <baseline-id> \
  --experiment-id <clean-context-id> \
  --experiment-id <refusal-aware-id> \
  --experiment-id <clean-refusal-id> \
  --format markdown \
  --out ../reports/medeval_v1_comparison_report.md
```

What this demonstrates: deterministic regression comparisons across retrieval
and refusal-control variants. Refusal-aware variants are controls, not real model
capability claims.

## 8. Start The Frontend

In one terminal:

```bash
cd backend
source .venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

- `http://localhost:3000`
- `http://localhost:3000/experiments`
- `http://localhost:3000/failures`
- `http://localhost:3000/human-review`
- `http://localhost:3000/reports`

What this demonstrates: experiment inspection, failure analysis, trace viewing,
report previews, and reviewer-facing calibration workflow.

## 9. Review Calibration Workflow

Generate a packet:

```bash
medeval export-review-packet \
  --experiment-id <experiment-id> \
  --out ../reports/examples/medeval_v1_review_packet_50.pending.json \
  --format json \
  --limit 50 \
  --strategy failure_priority
```

Validate it:

```bash
medeval validate-review-packet \
  --path ../reports/examples/medeval_v1_review_packet_50.pending.json
```

After manual completion, import:

```bash
medeval import-review-packet \
  --path ../reports/examples/medeval_v1_review_packet_50.completed.json \
  --reviewer-label "mohit_manual_review"
```

Check progress and export summary:

```bash
medeval review-progress --experiment-id <experiment-id>
medeval export-review-summary \
  --experiment-id <experiment-id> \
  --format markdown \
  --out ../reports/medeval_v1_manual_review_summary.md
```

What this demonstrates: curated manual review, validation, import, progress
tracking, and calibration summaries. Current committed labels are manual
self-review calibration labels, not clinician review or clinical validation.

## 10. Run The Full Smoke Workflow

From the repository root:

```bash
make medeval-v1-smoke
```

What this demonstrates: the full reproducible artifact loop from dataset
validation through deterministic runs and report checking.

## What To Say During The Demo

MedEval is an open-source healthcare RAG evaluation suite for measuring
groundedness, citation quality, refusal behavior, retrieval quality, and failure
modes on public healthcare documents.

MedEval v1 is in development. It includes public-source seed documents,
evidence-linked QA, deterministic reproducibility, rich failure diagnostics, and
self-reviewed calibration labels. It is not medical advice, clinical
validation, clinician review, production evidence, or an external adoption
claim.
