# Architecture

MedEval is planned as a modular healthcare RAG evaluation platform. Batch 1 adds
the first real backend data and retrieval foundation while keeping answer
generation and evaluation metrics out of scope.

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

## Batch 1 Backend Flow

- Documents are created from JSON or uploaded text/markdown/PDF files.
- Text is cleaned conservatively to preserve evidence and section wording.
- Documents are chunked deterministically with character offsets.
- Chunks are embedded using `deterministic-hash-embedding-384` by default.
- PostgreSQL stores embeddings in a pgvector-compatible `vector(384)` column.
- SQLite tests use an isolated JSON-text vector fallback.
- Retrieval embeds the query, applies optional filters, scores chunks, returns
  top-k results, and stores lightweight retrieval query/result logs.

## Current Boundaries

The current implementation does not generate answers, score QA benchmarks,
perform clinical validation, or report benchmark results.
