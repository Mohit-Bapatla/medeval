# Recruiting Notes

This document helps describe MedEval accurately in resumes, interviews, and
project writeups. Do not claim real users, external adoption, clinical
validation, healthcare validation, production use, or benchmark results.

## Resume Bullet Variants

Backend / infrastructure focused:

- Built MedEval, an open-source FastAPI/PostgreSQL/pgvector evaluation platform
  for reproducible RAG experiments, trace storage, metric computation, YAML
  configs, CLI workflows, and report exports over synthetic healthcare QA data.

AI / RAG evaluation focused:

- Developed a RAG reliability harness that measures retrieval quality, citation
  grounding, refusal behavior, hallucination flags, claim support, and
  retrieval-vs-generation failure modes using deterministic local providers and
  evidence-linked QA examples.

Full-stack / product focused:

- Built a full-stack evaluation dashboard with Next.js, TypeScript, FastAPI, and
  PostgreSQL for inspecting RAG experiments, response traces, retrieved/cited
  chunks, failure analysis, human reviews, and Markdown/JSON/CSV reports.

## 30-Second Pitch

MedEval is an open-source healthcare-adjacent RAG evaluation platform. It is not
a chatbot; it is a harness for testing whether a RAG system retrieves the right
evidence, answers with grounded citations, refuses unsupported questions, and
exposes failure modes through traces, metrics, dashboards, and reports.

## 60-Second Pitch

MedEval is a full-stack evaluation system for RAG/LLM reliability. It ingests
documents, chunks and embeds them, stores vectors in pgvector, imports
evidence-linked QA examples, runs deterministic local RAG experiments, stores
response traces, evaluates citations/refusals/retrieval/claim support, and
surfaces failures in a dashboard. The sample dataset is synthetic and the
current evaluator is heuristic, so the project is honest about its limits while
still demonstrating the infrastructure needed for rigorous AI evaluation.

## Technical Talking Points

- FastAPI service boundaries and Pydantic API contracts
- SQLAlchemy models and Alembic migrations for experiment data
- PostgreSQL + pgvector retrieval
- Deterministic local embeddings and answer providers for no-key reproducibility
- Evidence-linked QA examples and JSONL import
- Trace-first RAG design
- Claim-level citation support heuristics
- Retrieval-vs-generation failure classification
- Typer CLI and YAML experiment configs
- Next.js dashboard and report exports

## What Not To Claim Yet

- Do not claim clinical validation.
- Do not claim healthcare validation.
- Do not claim real users or adoption.
- Do not claim production deployment.
- Do not claim real benchmark results.
- Do not imply the deterministic provider is a real LLM.
- Do not imply the heuristic evaluator is medically validated.

Use placeholders like `[X QA pairs]`, `[Y documents]`, and `[Z configs]` when
describing future scale or unpublished local runs.
