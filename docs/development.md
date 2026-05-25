# Development

## Safety Rules

- Do not commit `.env` files or real API keys.
- Use `.env.example` for placeholders only.
- Do not commit real patient data, private student data, or fabricated benchmark
  results.
- Keep examples fake, synthetic, or clearly marked as demo-only.

## Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python -m ruff check .
uvicorn app.main:app --reload --port 8000
```

## Frontend

```powershell
cd frontend
npm install
npm run typecheck
npm run dev
```

The frontend defaults to `http://localhost:8000/api/v1`. Set
`NEXT_PUBLIC_API_BASE_URL` only when pointing at another local backend; do not
commit a real `.env` file.

## Database

```powershell
cd C:\Users\MOHIT\Projects\medeval
Copy-Item .env.example .env
docker compose up -d db
cd backend
.\.venv\Scripts\python -m alembic upgrade head
.\.venv\Scripts\python -m alembic current
```

The first migration enables the PostgreSQL `vector` extension for pgvector. The
Batch 1 migration adds documents, chunks, retrieval queries, and retrieval
results. Batch 4 adds human review records. A local `.env` is ignored by git and
must not be committed.

## Document Retrieval Workflow

After the database is running and migrations are applied, create or upload a
document, chunk it, embed its chunks, and search retrieval:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/documents `
  -ContentType "application/json" `
  -Body '{"title":"Synthetic Demo","source_type":"synthetic_demo","document_type":"onboarding_doc","raw_text":"HIPAA training is required before badge access."}'

Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/documents/<document-id>/chunk
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/documents/<document-id>/embed
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/retrieval/search `
  -ContentType "application/json" `
  -Body '{"query":"HIPAA training badge access","top_k":5}'
```

Synthetic sample markdown files are available in `datasets/sample/documents/`.
The seed script can load, chunk, and embed them when a database is available:

```powershell
python scripts/seed_sample_documents.py
```

Then seed synthetic QA and run a local deterministic experiment:

```powershell
python scripts/seed_sample_qa.py
python scripts/run_sample_experiment.py
```

The experiment output is a local smoke summary for development. It is not a
validated benchmark result.

## Dashboard

Start the backend and frontend, then open `http://localhost:3000`:

```powershell
cd backend
.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

```powershell
cd frontend
npm.cmd run dev
```

Use `/traces/{responseId}` to inspect retrieved chunks, cited chunks, model
answer, gold answer, evaluator scores, failure type, and raw output.

## Batch 4 CLI Workflow

After installing the backend package, the `medeval` CLI can run deterministic
local workflows without external services:

```powershell
cd backend
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\medeval status
.\.venv\Scripts\medeval seed-docs --path ..\datasets\sample\documents
.\.venv\Scripts\medeval seed-qa --dataset-name "MedEval HealthcareQA Sample" --path ..\datasets\sample\qa\healthcare_qa_sample.jsonl
.\.venv\Scripts\medeval run-experiment --config ..\configs\experiments\baseline_deterministic.yaml
```

CLI report exports include limitations and should not be treated as validated
benchmark results.

## Batch 5 Demo Validation

Use `docs/demo-checklist.md` for the screenshot and manual validation sequence.
The checklist covers Docker/Postgres, migrations, backend health/status, CLI
seeding, deterministic experiment runs, dashboard pages, traces, failures, and
report exports.
