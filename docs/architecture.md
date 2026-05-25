# Architecture

MedEval is a modular evaluation platform for healthcare-adjacent RAG and LLM
systems. It is built to inspect reliability, evidence grounding, citation
behavior, retrieval quality, refusals, traces, and reports. It is not a chatbot
and it does not claim clinical validation.

## High-Level Flow

```mermaid
flowchart LR
  A["Synthetic or governed documents"] --> B["Text cleaning"]
  B --> C["Deterministic chunking"]
  C --> D["Embedding provider"]
  D --> E["PostgreSQL + pgvector"]
  E --> F["Retriever"]
  F --> G["RAG answer provider"]
  G --> H["Model response trace"]
  H --> I["Evaluation harness"]
  I --> J["Experiment results"]
  J --> K["Dashboard + reports"]
```

## Backend Service Layers

- **API layer**: FastAPI routes under `/api/v1` for documents, retrieval,
  datasets, QA examples, prompts, RAG answers, responses, evaluations,
  experiments, reports, dashboard summary, and human reviews.
- **Schema layer**: Pydantic request/response models keep API shapes explicit.
- **Service layer**: ingestion, text cleaning, chunking, embeddings, retrieval,
  datasets, prompt rendering, deterministic answer generation, RAG traces,
  evaluation, experiment execution, reporting, config loading, and CLI support.
- **Evaluation layer**: deterministic correctness, grounding, citation,
  retrieval, refusal, hallucination, failure taxonomy, and claim-support
  heuristics.
- **Persistence layer**: SQLAlchemy models and Alembic migrations for
  PostgreSQL/pgvector, with isolated SQLite test fallbacks where needed.

## Database Entities

```mermaid
erDiagram
  documents ||--o{ document_chunks : contains
  documents ||--o{ qa_examples : references
  datasets ||--o{ qa_examples : contains
  qa_examples ||--o{ evidence_links : expects
  document_chunks ||--o{ evidence_links : supports
  experiments ||--o{ model_responses : produces
  qa_examples ||--o{ model_responses : answered_by
  model_responses ||--o{ response_retrieved_chunks : stores
  document_chunks ||--o{ response_retrieved_chunks : retrieved_as
  model_responses ||--o{ evaluation_results : evaluated_by
  model_responses ||--o{ human_reviews : reviewed_by
  prompt_templates ||--o{ experiments : configures
  prompt_templates ||--o{ model_responses : used_for
```

Core tables include documents, document chunks, retrieval logs, datasets, QA
examples, evidence links, prompt templates, experiments, model responses,
response retrieved chunks, evaluation results, and human reviews.

## Retrieval Flow

```mermaid
sequenceDiagram
  participant User
  participant API
  participant RetrievalService
  participant Embeddings
  participant DB as PostgreSQL/pgvector

  User->>API: POST /retrieval/search
  API->>RetrievalService: query + filters
  RetrievalService->>Embeddings: embed query
  Embeddings-->>RetrievalService: deterministic vector
  RetrievalService->>DB: vector similarity search
  DB-->>RetrievalService: ranked chunks
  RetrievalService-->>API: chunks + scores + metadata
  API-->>User: retrieval response
```

The default development embedding provider is deterministic and local. It is
useful for tests and sample demos, but it is not a semantic embedding model for
real evaluation.

## RAG And Evaluation Flow

```mermaid
sequenceDiagram
  participant Runner
  participant RAG
  participant Retriever
  participant Provider as Deterministic answer provider
  participant Evaluator
  participant DB

  Runner->>RAG: QA example + experiment config
  RAG->>Retriever: retrieve top-k chunks
  Retriever-->>RAG: evidence candidates
  RAG->>Provider: prompt + question + chunks
  Provider-->>RAG: structured answer + citations
  RAG->>DB: store response trace
  RAG->>Evaluator: response + evidence links + retrieved chunks
  Evaluator-->>DB: store scores, claim support, failure metadata
```

The deterministic answer provider never uses the gold answer to generate a
response. It exists so developers can run the full loop without paid APIs or
external services.

## Experiment And Report Flow

```mermaid
flowchart TD
  A["YAML experiment config"] --> B["Typer CLI or API"]
  B --> C["Experiment service"]
  C --> D["Run QA examples synchronously"]
  D --> E["Store responses and evaluations"]
  E --> F["Aggregate metrics"]
  F --> G["Dashboard"]
  F --> H["Markdown report"]
  F --> I["JSON report"]
  F --> J["CSV results"]
```

Experiments are synchronous and small-dataset oriented today. Reports are
computed from the local database and include limitations/disclaimers.

## Frontend Dashboard Flow

The Next.js dashboard uses a typed fetch client pointed at
`NEXT_PUBLIC_API_BASE_URL`, defaulting to `http://localhost:8000/api/v1`.
Dashboard pages read backend state directly:

- overview summary counts
- documents and chunks
- datasets, QA examples, and evidence links
- experiments and aggregate metrics
- response traces with retrieved/cited chunks
- claim support and failure metadata
- report previews and downloads

Empty states explain how to seed sample data instead of hardcoding fake metrics.

## CLI Flow

The Typer CLI wraps repeatable local demo workflows:

```mermaid
flowchart LR
  A["medeval status"] --> B["seed-docs"]
  B --> C["seed-qa"]
  C --> D["run-experiment"]
  D --> E["export-report"]
  D --> F["export-results"]
```

CLI commands respect the configured `DATABASE_URL`, do not require API keys, and
are intended for synthetic local demo runs unless a future governed data process
is added.

## Boundaries

- No real patient data is included.
- No private student data is included.
- No real provider APIs are called by tests or local deterministic workflows.
- Current metrics are heuristic and not clinically validated.
- Synthetic sample outputs are not benchmark results.
