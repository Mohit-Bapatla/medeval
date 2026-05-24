# Roadmap

## Batch 0: Foundation

- Monorepo structure
- FastAPI backend skeleton
- Next.js frontend skeleton
- PostgreSQL/pgvector Docker Compose setup
- Alembic foundation
- Documentation and development workflow

## Batch 1: Core Data Model

- Projects, datasets, documents, chunks, questions, experiment runs, traces, and
  metric result tables
- Initial sample dataset format using fake/demo data only
- Database migrations and seed examples

## Batch 2: Dataset And Document Pipeline

- Dataset import validation
- Document ingestion
- Text cleaning and chunking
- Safe sample fixtures

## Batch 3: Retrieval And Generation

- Embedding provider abstraction
- Vector storage and retrieval
- RAG answer generation with citation capture
- Provider interfaces without committed secrets

## Batch 4: Evaluation And Reports

- Metric implementations
- Experiment runner
- Failure classification
- Report export
- Dashboard views for comparing runs
