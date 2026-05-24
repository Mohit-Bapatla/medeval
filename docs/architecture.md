# Architecture

MedEval is planned as a modular healthcare RAG evaluation platform. Batch 0
establishes the backend, frontend, database, and documentation foundation without
committing to a detailed production schema.

## Planned Layers

- Data/document layer: ingest source documents, clean text, chunk content, and
  track safe dataset provenance for fake/demo or properly governed data.
- Retrieval layer: create embeddings, store vectors in PostgreSQL with pgvector,
  run retrieval experiments, and record retrieved evidence.
- Generation layer: call model providers through an abstraction that supports
  answer generation, citations, refusals, latency tracking, and cost estimates.
- Evaluation layer: compute correctness, groundedness, hallucination, refusal,
  citation, and retrieval metrics.
- Experiment/reporting layer: run reproducible evaluations, store traces and
  failures, compare runs, and export reports.
- Dashboard layer: provide a focused UI for experiments, traces, metrics, and
  reports rather than a generic chatbot.

## Batch 0 Boundaries

The initial implementation includes API health/status endpoints, settings,
database connection plumbing, Alembic setup, a minimal Next.js shell, Docker
Compose for PostgreSQL/pgvector, and project documentation.
