# Architecture

MedEval is planned as a modular healthcare RAG evaluation platform. Batch 2 adds
the first QA benchmark, deterministic RAG trace, evaluation, and experiment
foundation while keeping paid providers and advanced judges out of scope.

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

The current implementation uses deterministic local answer generation and MVP
heuristic evaluators. It does not call real provider APIs, perform clinical
validation, or report validated benchmark results.

## Batch 2 Evaluation Flow

- Datasets contain QA examples with answerability, category, difficulty, risk,
  gold answers, and optional expected behavior.
- Evidence links connect QA examples to required, acceptable, or supporting
  chunks.
- RAG traces store retrieved chunks, cited chunks, provider output, latency,
  token estimates, and estimated cost.
- Evaluation results store deterministic heuristic retrieval, citation, refusal,
  correctness, groundedness, hallucination, failure type, and overall scores.
- Experiments synchronously run a small dataset through RAG and evaluation, then
  expose aggregate metrics.

## Batch 3 Dashboard Layer

- The frontend reads typed API responses from the local FastAPI backend.
- Overview counts, experiment metrics, failure analysis, traces, and reports are
  computed from stored backend data.
- The trace viewer is the primary inspection surface: it shows question, gold
  answer, model answer, retrieved chunks, cited chunks, scores, failure type,
  provider metadata, and raw structured output.
- Report previews are computed Markdown/JSON responses and are not persisted
  artifacts in Batch 3.

## Batch 4 Evaluation And Workflow Layer

- Claim extraction and citation support checks live in `backend/app/evals/` as
  deterministic heuristics.
- Evaluation results keep claim-support metrics and failure analysis details in
  `metadata_json` so the schema remains flexible.
- Human review records are stored separately because they are authored records,
  not derived evaluator output.
- YAML configs and the CLI provide reproducible local runs over synthetic data.
- Report exports are computed from stored experiments and always include
  limitations and non-validation disclaimers.
