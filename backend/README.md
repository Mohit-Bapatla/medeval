# MedEval Backend

FastAPI service for MedEval. The backend includes health/status endpoints,
document ingestion, conservative text cleaning, deterministic chunking,
deterministic local embeddings, pgvector-ready vector storage, retrieval search,
retrieval logs, synthetic QA datasets, deterministic RAG traces, MVP evaluation
results, synchronous experiment runs, Alembic migrations, and tests.

## Local Development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest
ruff check .
uvicorn app.main:app --reload --port 8000
```

The backend reads configuration from environment variables. A root `.env.example`
is provided for local placeholders; do not commit real secrets.

## Batch 1 Workflow

1. Create a document with `POST /api/v1/documents` or upload a `.txt`, `.md`, or
   best-effort text PDF with `POST /api/v1/documents/upload`.
2. Chunk it with `POST /api/v1/documents/{document_id}/chunk`.
3. Embed chunks with `POST /api/v1/documents/{document_id}/embed` or
   `POST /api/v1/chunks/embed`.
4. Search chunks with `POST /api/v1/retrieval/search`.

The default embedding provider is `deterministic-hash-embedding-384`. It is
stable, normalized, local, and keyless so tests and local retrieval do not need
paid model APIs.

## Batch 2 Workflow

1. Create a dataset with `POST /api/v1/datasets`.
2. Add QA examples with `POST /api/v1/datasets/{dataset_id}/examples` or import
   JSONL with `POST /api/v1/datasets/{dataset_id}/import-jsonl`.
3. Link expected evidence chunks with
   `POST /api/v1/qa-examples/{qa_example_id}/evidence-links`.
4. Generate a deterministic local RAG answer with `POST /api/v1/rag/answer`.
5. Evaluate a response with `POST /api/v1/responses/{model_response_id}/evaluate`.
6. Create and run a small synchronous experiment with `POST /api/v1/experiments`
   and `POST /api/v1/experiments/{experiment_id}/run`.

## Batch 3 Dashboard Endpoints

- `GET /api/v1/dashboard/summary`
- `GET /api/v1/experiments/{experiment_id}/responses`
- `GET /api/v1/experiments/{experiment_id}/failures`
- `GET /api/v1/experiments/{experiment_id}/report`
- `GET /api/v1/responses/{model_response_id}/trace`

These endpoints compute dashboard, trace, failure, and report views from existing
experiment data. They do not persist report artifacts or fabricate metrics.

## Batch 4 CLI And Evaluation Polish

Batch 4 adds deterministic claim extraction and citation-support heuristics,
richer failure taxonomy metadata, retrieval-vs-generation failure labels, human
review records, YAML experiment configs, Typer CLI commands, and
Markdown/JSON/CSV report exports.

CLI examples:

```powershell
.\.venv\Scripts\medeval status
.\.venv\Scripts\medeval seed-docs --path ..\datasets\sample\documents
.\.venv\Scripts\medeval seed-qa --dataset-name "Synthetic Healthcare Opportunity QA" --path ..\datasets\sample\qa\healthcare_qa_sample.jsonl
.\.venv\Scripts\medeval run-experiment --config ..\configs\experiments\baseline_deterministic.yaml
```

New API endpoints:

- `POST /api/v1/experiments/from-config`
- `GET /api/v1/experiments/{experiment_id}/results.csv`
- `POST /api/v1/responses/{response_id}/human-review`
- `GET /api/v1/responses/{response_id}/human-reviews`

Claim support and failure labels are deterministic heuristics stored in
`evaluation_results.metadata_json`. They are not validated benchmark metrics or
clinical review.

## Limitations

- No answer generation, QA benchmark import, experiment runner, or metric scoring
  using paid providers or LLM judges is implemented in Batch 2.
- PDF upload is text extraction only; OCR and layout recovery are out of scope.
- The deterministic embedding provider is for development and reproducibility,
  not validated semantic benchmark performance.
- The deterministic answer provider and MVP evaluator are local/dev/test
  scaffolding, not benchmark-grade or clinically validated evaluation.
- Human review records are manually created records; no fake reviews are seeded.
