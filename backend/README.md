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

## Limitations

- No answer generation, QA benchmark import, experiment runner, or metric scoring
  using paid providers or LLM judges is implemented in Batch 2.
- PDF upload is text extraction only; OCR and layout recovery are out of scope.
- The deterministic embedding provider is for development and reproducibility,
  not validated semantic benchmark performance.
- The deterministic answer provider and MVP evaluator are local/dev/test
  scaffolding, not benchmark-grade or clinically validated evaluation.
