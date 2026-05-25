# MedEval Technical Report

## Abstract

MedEval is an open-source evaluation and reliability platform for
healthcare-adjacent RAG and LLM systems. It focuses on reproducible experiments,
retrieval traces, citation grounding, refusal behavior, failure analysis, and
report exports. The current implementation uses synthetic sample data,
deterministic local providers, and heuristic evaluators for development and
demo workflows.

## Problem

RAG systems can produce confident answers that are unsupported, weakly cited, or
incorrectly refused. In healthcare-adjacent contexts, teams need infrastructure
that records evidence, citations, evaluator decisions, failure modes, and
reproducible experiment configs.

## Dataset

The repository includes MedEval HealthcareQA Sample v0.1, a synthetic local demo
dataset with 5 documents and 22 QA examples. The data covers healthcare
opportunity and onboarding scenarios such as eligibility, deadlines, required
documents, HIPAA training, schedules, locations, and unanswerable questions.

The sample contains no real patient data, private student data, clinical records,
or real organization claims.

## Architecture

MedEval uses a FastAPI backend, SQLAlchemy/Alembic persistence, PostgreSQL with
pgvector for vector search, deterministic local providers for development, a
Typer CLI for reproducible workflows, and a Next.js dashboard for inspection.

```mermaid
flowchart LR
  A["Documents"] --> B["Chunks"]
  B --> C["Embeddings"]
  C --> D["pgvector retrieval"]
  D --> E["RAG trace"]
  E --> F["Evaluation"]
  F --> G["Experiment aggregation"]
  G --> H["Dashboard and reports"]
```

## Evaluation Metrics

Current metrics include correctness, groundedness, citation precision/recall,
retrieval precision/recall, refusal accuracy, hallucination flags, claim support
rate, unsupported claim rate, latency, estimated cost, and failure labels.

These metrics are deterministic development heuristics. They are not clinically
validated and are not a substitute for human, clinician, or benchmark-grade
evaluation.

## Experiment Setup

Local experiments are configured through YAML files in `configs/experiments/`.
The baseline deterministic config runs the synthetic QA sample through local
retrieval, a deterministic answer provider, trace storage, and heuristic
evaluation.

## Sample Deterministic Run

The local demo can generate an example synthetic deterministic run from the
checked-in sample data. Any metrics from that run must be labeled:

> Example synthetic deterministic run from local demo, not validated benchmark
> results.

This report intentionally does not publish fixed benchmark scores.

## Failure Analysis

MedEval separates retrieval failures from generation/evaluation failures where
possible. Failure metadata can include primary and secondary failure types,
evidence summaries, retrieval failure flags, generation failure flags, and
claim-level support details.

## Limitations

- Synthetic sample data only
- Deterministic answer provider, not a real LLM
- Heuristic evaluator, not benchmark-grade
- No clinical validation
- No production-use claim
- No external adoption claim
- No real provider calls in local tests/demo workflows

## Future Work

- Real provider adapters
- Larger and reviewed benchmark datasets
- Human and clinician review workflows
- LLM-as-judge experiments with auditability
- Reranking and retrieval strategy comparisons
- CI/CD and deployment hardening
- Formal open-source benchmark reports with clear methodology
