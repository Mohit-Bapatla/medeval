# Benchmark Card: MedEval HealthcareQA Sample v0.1

## Status

This is a synthetic/demo dataset card for local MedEval development. It is not a
validated benchmark, clinical evaluation, healthcare validation artifact, or
evidence of production use.

## Dataset Name

MedEval HealthcareQA Sample v0.1

## Purpose

The sample exercises MedEval workflows for document ingestion, retrieval,
citation-grounded answering, response tracing, deterministic heuristic
evaluation, failure analysis, and report export.

## Source

All documents and QA examples are handcrafted synthetic demo content stored in
this repository:

- `datasets/sample/documents/`
- `datasets/sample/qa/healthcare_qa_sample.jsonl`

## Synthetic Status

The dataset is entirely synthetic. It does not contain real patient data,
private student data, real organization records, or real clinical evidence.

## Current Contents

- Documents: 5 synthetic healthcare opportunity/onboarding documents
- QA examples: 22 synthetic QA examples
- Answerability split in the checked-in JSONL:
  - answerable: 18
  - unanswerable: 4
- Topic categories include:
  - application process
  - benefits
  - boundaries
  - deadlines
  - eligibility
  - HIPAA training
  - limitations
  - location
  - onboarding
  - privacy
  - required documents
  - role responsibilities
  - role scope
  - schedule

## Intended Use

- Local development smoke tests
- Contributor onboarding
- Demonstrating trace, evaluation, failure analysis, and report workflows
- Testing deterministic local providers without paid APIs

## Out-Of-Scope Use

- Clinical validation
- Healthcare safety claims
- Production readiness claims
- Measuring real-world provider performance
- Publishing benchmark results without a separately reviewed dataset, protocol,
  and evaluation process

## Evaluation Notes

The sample can be used to run a deterministic local demo experiment. Any scores
from that run are synthetic local development output, not validated benchmark
results.

## Safety And Privacy

- No real patient data
- No private student data
- No secrets
- No real healthcare organization records
- No clinical review claim

## License Note

The sample data is part of this MIT-licensed repository unless a future dataset
release states otherwise.

## Limitations

- The dataset is intentionally small.
- The deterministic answer provider is not a real LLM.
- The deterministic evaluator uses heuristic overlap and citation checks.
- Evidence links are designed for local demo traceability, not clinical review.
- Results generated from this sample should be labeled as synthetic deterministic
  demo output.
