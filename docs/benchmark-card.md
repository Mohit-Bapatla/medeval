# MedEval HealthcareQA Sample v0.1

## Status

This is a synthetic/demo benchmark card for local MedEval development. It is not a
validated healthcare benchmark, clinical evaluation, or evidence of production use.

## Purpose

The sample is designed to exercise MedEval workflows for document ingestion,
retrieval, citation-grounded answering, response tracing, deterministic heuristic
evaluation, failure analysis, and report export.

## Data

- Documents: synthetic healthcare opportunity and onboarding documents under
  `datasets/sample/documents/`
- QA examples: synthetic examples under
  `datasets/sample/qa/healthcare_qa_sample.jsonl`
- Domains covered: eligibility, deadlines, required documents, scheduling,
  HIPAA/onboarding, application process, location, and unanswerable questions
- Data excluded: real patient data, private student data, real organization
  claims, and real benchmark results

## Intended Use

- Local development smoke tests
- Demonstrating trace, evaluation, and report workflows
- Reproducible deterministic examples for contributors

## Not Intended Use

- Clinical validation
- Healthcare safety claims
- Measuring real-world provider performance
- Reporting benchmark results without a separately reviewed dataset and protocol

## Limitations

- All content is synthetic and intentionally small.
- The deterministic answer provider is not a real LLM.
- The deterministic evaluator uses heuristic token overlap and citation checks.
- Results generated from this sample are development artifacts, not benchmark
  claims.
