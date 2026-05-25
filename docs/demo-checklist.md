# MedEval Local Demo And Screenshot Checklist

This checklist is for a synthetic local demo only. It does not produce validated
benchmark results, clinical validation, healthcare validation, adoption claims,
or production-use claims.

## Recommended Capture Setup

- Browser viewport: 1440 x 1000 or similar desktop size
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`
- Data: synthetic seeded sample documents and QA only
- Suggested output directory: `docs/assets/screenshots/`

## Setup

- [ ] Confirm Docker is available: `docker --version`
- [ ] Confirm Docker Compose is available: `docker compose version`
- [ ] Confirm the Docker daemon is running.
- [ ] From the repo root, create a local ignored env file if needed:
  `Copy-Item .env.example .env`
- [ ] Start Postgres/pgvector: `docker compose up -d db`
- [ ] Install backend dependencies:
  `cd backend; .\.venv\Scripts\python -m pip install -e ".[dev]"`
- [ ] Apply migrations:
  `.\.venv\Scripts\python -m alembic upgrade head`
- [ ] Confirm migration head:
  `.\.venv\Scripts\python -m alembic current`

## Seed And Run

- [ ] Run `.\.venv\Scripts\medeval status`
- [ ] Seed documents:
  `.\.venv\Scripts\medeval seed-docs --path ..\datasets\sample\documents`
- [ ] Seed QA:
  `.\.venv\Scripts\medeval seed-qa --dataset-name "MedEval HealthcareQA Sample" --path ..\datasets\sample\qa\healthcare_qa_sample.jsonl`
- [ ] Run experiment:
  `.\.venv\Scripts\medeval run-experiment --config ..\configs\experiments\baseline_deterministic.yaml`
- [ ] Copy the generated experiment ID for trace and report validation.

## Run The Apps

- [ ] Start backend:
  `.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000`
- [ ] Confirm `http://localhost:8000/health`
- [ ] Confirm `http://localhost:8000/api/v1/status`
- [ ] Confirm `http://localhost:8000/docs`
- [ ] Start frontend:
  `cd frontend; npm.cmd run dev`
- [ ] Open `http://localhost:3000`

## Screenshot Filename Checklist

Use these exact filenames when refreshing screenshots:

- [ ] `01-overview-dashboard.png` - overview dashboard with seeded counts and status
- [ ] `02-documents-page.png` - document list with synthetic documents
- [ ] `03-document-detail-chunks.png` - document metadata and chunk list
- [ ] `04-datasets-page.png` - dataset list
- [ ] `05-dataset-detail-qa.png` - QA examples with answerability/category labels
- [ ] `06-experiments-page.png` - experiment list
- [ ] `07-experiment-detail-metrics.png` - aggregate experiment metrics and charts
- [ ] `08-trace-viewer.png` - question, gold answer, model answer, retrieved/cited chunks
- [ ] `09-claim-support-and-evidence.png` - claim support and evidence metadata
- [ ] `10-failure-analysis.png` - failure counts and failed response table
- [ ] `11-reports-page.png` - reports landing/list page
- [ ] `12-experiment-report-preview.png` - computed experiment report preview

## Export Checks

- [ ] Markdown report:
  `.\.venv\Scripts\medeval export-report --experiment-id <experiment-id> --format markdown --out ..\reports\sample_deterministic_report.md`
- [ ] JSON report:
  `.\.venv\Scripts\medeval export-report --experiment-id <experiment-id> --format json --out ..\reports\sample_deterministic_report.json`
- [ ] CSV results:
  `.\.venv\Scripts\medeval export-results --experiment-id <experiment-id> --format csv --out ..\reports\sample_deterministic_results.csv`
- [ ] Confirm every report includes limitations and disclaimers.
- [ ] Keep generated reports local unless intentionally adding a clearly labeled
  synthetic artifact.

## Final Validation

- [ ] Backend tests pass: `.\.venv\Scripts\python -m pytest`
- [ ] Ruff passes: `.\.venv\Scripts\python -m ruff check .`
- [ ] Alembic heads works: `.\.venv\Scripts\python -m alembic heads`
- [ ] Frontend typecheck passes: `npm.cmd run typecheck`
- [ ] Frontend build passes: `npm.cmd run build`
- [ ] `git diff --check` passes
- [ ] `git status -sb` contains only intentional changes

## Troubleshooting

- Docker daemon unavailable: start Docker Desktop, then rerun
  `docker compose up -d db`.
- Port `5432` already in use: set `POSTGRES_PORT` in a local ignored `.env`, or
  stop the conflicting local Postgres service.
- DB connection refused: confirm `docker compose ps` shows the `db` service as
  healthy, then rerun Alembic and `medeval status`.
- Migration failure: capture the Alembic error, avoid deleting volumes without
  reviewing local data, and rerun against a fresh demo database if needed.
- Frontend cannot reach API: confirm `NEXT_PUBLIC_API_BASE_URL` includes
  `/api/v1`, then restart `npm.cmd run dev`.
- Duplicate sample data: `seed-docs` skips existing documents and `seed-qa`
  skips an existing populated sample dataset. Use a fresh database for a clean
  demo replay.
