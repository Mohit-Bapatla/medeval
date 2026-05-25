# Roadmap

## Batch 0: Foundation

- Monorepo structure
- FastAPI backend skeleton
- Next.js frontend skeleton
- PostgreSQL/pgvector Docker Compose setup
- Alembic foundation
- Documentation and development workflow

## Batch 1: Core Data Model

- Documents, chunks, deterministic local embeddings, retrieval queries, and
  retrieval result logs
- Synthetic sample healthcare opportunity and onboarding documents
- Document ingestion, chunking, embedding, and retrieval APIs

## Batch 2: Dataset And Document Pipeline

- QA benchmark dataset schema and JSONL import/export
- Evidence links from QA examples to chunks
- Deterministic local RAG answer traces
- MVP evaluation result schema and synchronous experiment runner
- Synthetic sample QA fixtures

## Batch 3: Retrieval And Generation

- Frontend dashboard
- Documents, datasets, experiments, trace viewer, failures, and reports pages
- Backend summary, trace, failure, response listing, and report endpoints
- Recharts visualizations for local experiment metrics

## Batch 4: Evaluation And Reports

- Deterministic claim-level citation support heuristics
- Retrieval-vs-generation failure separation and richer taxonomy metadata
- Human review records for model responses
- YAML experiment configs and Typer CLI workflow
- Markdown, JSON, and CSV report exports with limitations
- Scoped frontend filtering, trace, review, and report download polish

Future batches can add governed provider integrations, comparison workflows, and
stronger evaluation methods without committing secrets or claiming validation
from synthetic samples.
