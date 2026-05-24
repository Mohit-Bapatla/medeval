# MedEval — Healthcare RAG Evaluation & Reliability Platform

MedEval is an open-source foundation for evaluating healthcare RAG and LLM systems
with reproducible datasets, traces, metrics, experiments, and reports.

This repository is in early development. It does not contain validated benchmark
results, healthcare validation, real patient data, private student data, user
adoption claims, or production readiness claims.

## Problem

Healthcare RAG systems need more than a working chat interface. Teams need to
measure whether answers are correct, grounded in retrieved evidence, appropriately
refused, accurately cited, reproducible, and operationally feasible.

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

The Batch 0 foundation is a monorepo:

- `backend/`: FastAPI service, API routes, settings, database session, Alembic, tests
- `frontend/`: Next.js TypeScript app with a minimal dashboard shell
- `docs/`: architecture, roadmap, dataset schema, metrics, and development notes
- `datasets/sample/`: safe sample-data location for future fake/demo examples
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

## Repository Structure

```text
backend/              FastAPI backend and tests
frontend/             Next.js dashboard shell
docs/                 Project documentation
datasets/sample/      Future fake/demo sample datasets
configs/experiments/  Future experiment configs
reports/              Generated local reports
scripts/              Utility scripts added in later batches
docker-compose.yml    Local PostgreSQL + pgvector
.env.example          Placeholder local configuration
```

## Roadmap

Batch 0 creates the project foundation. Later batches will add database schema,
dataset import, document ingestion, retrieval, answer generation, evaluation
metrics, trace storage, reports, dashboard workflows, and CLI commands.

## Safety And Privacy

Do not commit real secrets, real patient data, private student data, or local
`.env` files. Use fake/demo/sample data only unless a future governed workflow
explicitly defines safe handling requirements.

## Status Disclaimer

MedEval is an early development repository. Any current UI labels, docs, or
schemas describe planned capabilities and local scaffolding only; they are not
validated healthcare benchmarks or clinical evidence.
