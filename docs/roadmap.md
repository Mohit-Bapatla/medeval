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

- Richer evaluator implementations
- Provider integrations without committed secrets
- Report export formats beyond Markdown/JSON preview
- Dashboard comparison workflows
