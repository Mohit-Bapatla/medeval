# Launch Post Draft

## GitHub / LinkedIn Draft

I built MedEval, an open-source evaluation and reliability platform for
healthcare-adjacent RAG/LLM systems.

MedEval is not a chatbot. It is an evaluation harness for checking whether RAG
systems retrieve the right evidence, answer with grounded citations, refuse
unsupported questions, and expose failure modes through traces, metrics,
dashboards, and reports.

Current capabilities include:

- FastAPI backend with PostgreSQL + pgvector
- document ingestion, chunking, deterministic local embeddings, and retrieval
- synthetic QA dataset import with evidence links
- deterministic local RAG answer traces
- citation, retrieval, refusal, hallucination, and claim-support heuristics
- failure taxonomy and retrieval-vs-generation failure classification
- YAML experiment configs and Typer CLI
- Next.js dashboard, trace viewer, failure analysis, and report exports

The checked-in sample dataset is synthetic demo data only. It contains no real
patient data and does not represent clinical validation or benchmark-grade
results. The deterministic answer provider and evaluator exist so contributors
can run the full workflow locally without paid model APIs.

GitHub: [insert repository link]

Next steps: real provider adapters, larger reviewed datasets, richer evaluation
methods, human review workflows, and CI/CD hardening.
