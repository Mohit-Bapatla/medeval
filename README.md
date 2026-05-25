# MedEval - Healthcare RAG Evaluation & Reliability Platform

MedEval is an open-source foundation for evaluating healthcare RAG and LLM systems
with reproducible datasets, traces, metrics, experiments, and reports.

This repository is in early development. It does not contain validated benchmark
results, healthcare validation, real patient data, private student data, user
adoption claims, or production readiness claims.

## Problem

Healthcare RAG systems need more than a working chat interface. Teams need to
measure whether answers are correct, grounded in retrieved evidence,
appropriately refused, accurately cited, reproducible, and operationally
feasible.

## Solution

MedEval is planned as a modular evaluation platform for:

- QA dataset import and review
- document ingestion, cleaning, chunking, embeddings, and retrieval
- RAG answer generation with citations
- model provider abstraction
- correctness, groundedness, refusal, citation, retrieval, latency, and cost metrics
- experiment runs, trace storage, failure classification, and report export
- a dashboard and CLI workflow for local development and reproducible evaluation

## Architecture Overview

The current foundation is a monorepo:

- `backend/`: FastAPI service, document/retrieval models, API routes, Alembic, tests
- `frontend/`: Next.js TypeScript app with a minimal dashboard shell
- `docs/`: architecture, roadmap, dataset schema, metrics, and development notes
- `datasets/sample/`: synthetic demo documents for local ingestion/retrieval testing
- `configs/experiments/`: future experiment configuration examples
- `reports/`: generated report destination, with no real results committed

## Tech Stack

- Backend: Python, FastAPI, Pydantic, SQLAlchemy, Alembic, pytest, Ruff
- Database: PostgreSQL with pgvector
- Frontend: Next.js, TypeScript, Tailwind
- Infrastructure: Docker Compose

## Local Development Quickstart

```powershell
# From C:\Users\MOHIT\Projects\medeval
Copy-Item .env.example .env
docker compose up -d db
```

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest
uvicorn app.main:app --reload --port 8000
```

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` for the frontend and `http://localhost:8000/docs`
for the backend API docs.

## Batch 1 Retrieval Workflow

Create a document:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/documents `
  -ContentType "application/json" `
  -Body '{"title":"Synthetic Demo","source_type":"synthetic_demo","document_type":"onboarding_doc","raw_text":"HIPAA training is required before badge access.","metadata":{"demo":true}}'
```

Chunk, embed, and search:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/documents/<document-id>/chunk
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/documents/<document-id>/embed
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/retrieval/search `
  -ContentType "application/json" `
  -Body '{"query":"HIPAA training badge access","top_k":5}'
```

Batch 1 uses `deterministic-hash-embedding-384`, a local fixed-dimension
embedding provider that requires no API keys. Batch 2 adds synthetic QA datasets,
evidence links, deterministic local RAG answers, model response traces, MVP
heuristic evaluators, and a synchronous small-dataset experiment runner.

The deterministic answer provider is local development scaffolding. It is not a
real LLM, not benchmark-grade, and not clinical validation.

## Batch 2 QA And Experiment Workflow

After sample documents are seeded, chunked, and embedded, import synthetic QA and
run a local deterministic experiment:

```powershell
python scripts/seed_sample_documents.py
python scripts/seed_sample_qa.py
python scripts/run_sample_experiment.py
```

Useful API entry points:

- `POST /api/v1/datasets`
- `POST /api/v1/datasets/{dataset_id}/import-jsonl`
- `POST /api/v1/qa-examples/{qa_example_id}/evidence-links`
- `POST /api/v1/rag/answer`
- `POST /api/v1/responses/{model_response_id}/evaluate`
- `POST /api/v1/experiments/{experiment_id}/run`
- `GET /api/v1/experiments/{experiment_id}/results`

## Batch 3 Dashboard Workflow

Batch 3 adds a frontend dashboard for exploring the local evaluation database:

- overview counts and latest experiment status
- document and chunk inspection
- dataset and QA example review
- experiment metrics and response tables
- response trace viewer with retrieved/cited chunks and evaluator scores
- failure analysis
- computed Markdown/JSON experiment reports

Run the backend and frontend locally:

```powershell
cd backend
.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

```powershell
cd frontend
npm.cmd run dev
```

Open `http://localhost:3000`. If no data appears, seed the synthetic sample data
and run a deterministic local experiment:

```powershell
python scripts/seed_sample_documents.py
python scripts/seed_sample_qa.py
python scripts/run_sample_experiment.py
```

Visible metrics come from the connected local backend database. Empty states are
shown instead of fake results when the database has not been seeded.

## Batch 4 CLI, Reports, And Evaluator Polish

Batch 4 adds deterministic claim-level citation support checks, richer failure
taxonomy metadata, retrieval-vs-generation failure separation, human review
records, YAML experiment configs, CLI commands, and Markdown/JSON/CSV report
exports. These features remain local development scaffolding and do not create
validated benchmark or healthcare claims.

Example deterministic workflow:

```powershell
cd backend
.\.venv\Scripts\medeval status
.\.venv\Scripts\medeval seed-docs --path ..\datasets\sample\documents
.\.venv\Scripts\medeval seed-qa --dataset-name "Synthetic Healthcare Opportunity QA" --path ..\datasets\sample\qa\healthcare_qa_sample.jsonl
.\.venv\Scripts\medeval run-experiment --config ..\configs\experiments\baseline_deterministic.yaml
```

Reports can be exported after a local experiment:

```powershell
.\.venv\Scripts\medeval export-report --experiment-id <experiment-id> --format markdown --out ..\reports\example_report.md
.\.venv\Scripts\medeval export-results --experiment-id <experiment-id> --format csv --out ..\reports\results.csv
```

Claim-level support uses deterministic token overlap against cited retrieved
chunks. It is useful for debugging traces, but it is not medically validated or
benchmark-grade.

## Repository Structure

```text
backend/              FastAPI backend and tests
frontend/             Next.js dashboard shell
docs/                 Project documentation
datasets/sample/      Synthetic demo sample documents
configs/experiments/  Future experiment configs
reports/              Generated local reports
scripts/              Utility scripts
docker-compose.yml    Local PostgreSQL + pgvector
.env.example          Placeholder local configuration
```

## Roadmap

Batch 0 created the project foundation. Batch 1 added document storage,
chunking, embeddings, retrieval search, and synthetic sample documents. Batch 2
added QA benchmark workflow foundations, deterministic local RAG traces, MVP
evaluation results, and experiment aggregation. Batch 3 added the frontend
dashboard, trace viewer, failure analysis, and computed reports. Batch 4 adds
CLI/config workflows, claim-level heuristic checks, human review records, and
stronger report exports.

Later batches will improve evaluator quality, provider integrations, trace
review, reports, dashboard workflows, and CLI commands.

## Safety And Privacy

Do not commit real secrets, real patient data, private student data, or local
`.env` files. Use fake/demo/sample data only unless a future governed workflow
explicitly defines safe handling requirements.

## Status Disclaimer

MedEval is an early development repository. Any current UI labels, docs, or
schemas describe planned capabilities and local scaffolding only; they are not
validated healthcare benchmarks or clinical evidence.
