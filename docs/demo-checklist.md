# MedEval Local Demo Checklist

This checklist is for a synthetic local demo only. It does not produce validated
benchmark results, clinical validation, healthcare validation, adoption claims,
or production-use claims.

## Setup

- [ ] Confirm Docker is available: `docker --version`
- [ ] From the repo root, create a local ignored env file if needed:
  `Copy-Item .env.example .env`
- [ ] Start Postgres/pgvector: `docker compose up -d db`
- [ ] Install backend dependencies:
  `cd backend; .\.venv\Scripts\python -m pip install -e ".[dev]"`
- [ ] Apply migrations:
  `.\.venv\Scripts\python -m alembic upgrade head`
- [ ] Confirm migration head:
  `.\.venv\Scripts\python -m alembic current`

## Run The Apps

- [ ] Start backend:
  `.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000`
- [ ] Confirm `http://localhost:8000/health`
- [ ] Confirm `http://localhost:8000/api/v1/status`
- [ ] Confirm `http://localhost:8000/docs`
- [ ] Start frontend:
  `cd frontend; npm.cmd run dev`
- [ ] Open `http://localhost:3000`

## Seed And Run

- [ ] Run `.\.venv\Scripts\medeval status`
- [ ] Seed documents:
  `.\.venv\Scripts\medeval seed-docs --path ..\datasets\sample\documents`
- [ ] Seed QA:
  `.\.venv\Scripts\medeval seed-qa --dataset-name "MedEval HealthcareQA Sample" --path ..\datasets\sample\qa\healthcare_qa_sample.jsonl`
- [ ] Run experiment:
  `.\.venv\Scripts\medeval run-experiment --config ..\configs\experiments\baseline_deterministic.yaml`
- [ ] Copy the generated experiment ID for trace/report validation.

## Screenshots To Capture

- [ ] Overview dashboard with seeded counts
- [ ] Documents page
- [ ] Document detail page with chunks
- [ ] Datasets page
- [ ] Dataset detail page with QA examples
- [ ] Experiments page
- [ ] Experiment detail page with aggregate metrics
- [ ] Trace viewer with question, gold answer, model answer, retrieved chunks,
  cited chunks, evaluator scores, claim support, and failure analysis
- [ ] Failure analysis page
- [ ] Report page
- [ ] Exported Markdown and CSV files opened locally

## Export Checks

- [ ] Markdown report:
  `.\.venv\Scripts\medeval export-report --experiment-id <experiment-id> --format markdown --out ..\reports\example_report.md`
- [ ] JSON report:
  `.\.venv\Scripts\medeval export-report --experiment-id <experiment-id> --format json --out ..\reports\example_report.json`
- [ ] CSV results:
  `.\.venv\Scripts\medeval export-results --experiment-id <experiment-id> --format csv --out ..\reports\results.csv`
- [ ] Confirm every report includes limitations/disclaimers.
- [ ] Keep generated reports local unless intentionally adding a clearly labeled
  synthetic artifact.

## Final Validation

- [ ] Backend tests pass: `.\.venv\Scripts\python -m pytest`
- [ ] Ruff passes: `.\.venv\Scripts\python -m ruff check .`
- [ ] Frontend typecheck passes: `npm.cmd run typecheck`
- [ ] Frontend build passes: `npm.cmd run build`
- [ ] `git diff --check` passes
- [ ] `git status -sb` contains only intentional Batch 5 changes
