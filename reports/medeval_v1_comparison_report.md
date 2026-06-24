# MedEval v1 Deterministic Comparison Report

Generated: 2026-06-24T01:55:32.440768+00:00

## Disclaimer

This report is computed from a local deterministic run over the connected database, including synthetic samples or the in-development MedEval v1 public healthcare seed dataset. It is not a validated benchmark, clinical validation, medical advice, healthcare validation, production-use evidence, or an external adoption claim.

This comparison is a deterministic local debugging/regression workflow for an in-development public healthcare seed dataset. It is not clinical validation, medical advice, or a validated leaderboard.

## Compared Experiments

| Experiment | ID | Status | Model | top_k | Examples |
| --- | --- | --- | --- | ---: | ---: |
| MedEval v1 Public Healthcare Seed - Deterministic Baseline | cb5c7d8d | completed | deterministic-extractive-answer-v1 | 5 | 92 |
| MedEval v1 Public Healthcare Seed - Clean Context Deterministic | a0145407 | completed | deterministic-extractive-answer-v1-clean-context | 5 | 92 |
| MedEval v1 Public Healthcare Seed - Metadata-Assisted Refusal Control | 356916bc | completed | deterministic-extractive-answer-v1-refusal-oracle | 5 | 92 |
| MedEval v1 Public Healthcare Seed - Clean Context Refusal Control | af1415ef | completed | deterministic-extractive-answer-v1-clean-refusal-oracle | 5 | 92 |

## Aggregate Metrics

| Experiment | Correctness | Groundedness | Citation Precision | Citation Recall | Retrieval Precision | Retrieval Recall | Refusal Accuracy | Hallucination Rate | Avg Latency | Cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| MedEval v1 Public Healthcare Seed - Deterministic Baseline | 0.292 | 0.989 | 0.800 | 0.907 | 0.180 | 0.976 | 0.870 | 0.130 | 0.000 | 0.000 |
| MedEval v1 Public Healthcare Seed - Clean Context Deterministic | 0.337 | 0.989 | 0.810 | 0.900 | 0.180 | 0.976 | 0.880 | 0.120 | 0.000 | 0.000 |
| MedEval v1 Public Healthcare Seed - Metadata-Assisted Refusal Control | 0.412 | 0.804 | 0.919 | 0.907 | 0.180 | 0.976 | 0.989 | 0.196 | 0.011 | 0.000 |
| MedEval v1 Public Healthcare Seed - Clean Context Refusal Control | 0.446 | 0.804 | 0.919 | 0.900 | 0.180 | 0.976 | 0.989 | 0.196 | 0.011 | 0.000 |

## Deltas Vs Baseline

| Experiment | Correctness Δ | Groundedness Δ | Citation Recall Δ | Retrieval Recall Δ | Refusal Accuracy Δ | Hallucination Rate Δ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| MedEval v1 Public Healthcare Seed - Deterministic Baseline | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| MedEval v1 Public Healthcare Seed - Clean Context Deterministic | +0.044 | +0.000 | -0.007 | +0.000 | +0.011 | -0.011 |
| MedEval v1 Public Healthcare Seed - Metadata-Assisted Refusal Control | +0.120 | -0.185 | +0.000 | +0.000 | +0.120 | +0.065 |
| MedEval v1 Public Healthcare Seed - Clean Context Refusal Control | +0.153 | -0.185 | -0.007 | +0.000 | +0.120 | +0.065 |

## Failure Type Counts

### MedEval v1 Public Healthcare Seed - Deterministic Baseline

- bad_citation: 8
- evaluator_insufficient_data: 6
- failed_to_refuse: 11
- missing_citation: 2
- none: 3
- over_refusal: 1
- partial_answer: 16
- wrong_answer: 45

### MedEval v1 Public Healthcare Seed - Clean Context Deterministic

- bad_citation: 8
- evaluator_insufficient_data: 7
- failed_to_refuse: 10
- missing_citation: 2
- none: 4
- over_refusal: 1
- partial_answer: 18
- wrong_answer: 42

### MedEval v1 Public Healthcare Seed - Metadata-Assisted Refusal Control

- bad_citation: 8
- failed_to_refuse: 17
- missing_citation: 2
- none: 3
- over_refusal: 1
- partial_answer: 16
- wrong_answer: 45

### MedEval v1 Public Healthcare Seed - Clean Context Refusal Control

- bad_citation: 8
- failed_to_refuse: 17
- missing_citation: 2
- none: 4
- over_refusal: 1
- partial_answer: 18
- wrong_answer: 42

## Rich Failure Diagnostics

### MedEval v1 Public Healthcare Seed - Deterministic Baseline

Failure categories:
- bad_synthesis: 45
- citation_mismatch: 21
- context_overload: 68
- failed_refusal: 11
- format_failure: 6
- incomplete_answer: 16
- missing_citation: 3
- over_refusal: 1
- retrieval_rank_failure: 6
- temporal_failure: 3

Failure stages:
- citation: 10
- format: 6
- generation: 16
- refusal: 12
- synthesis: 45

Severity:
- critical: 11
- high: 45
- low: 6
- medium: 27
- Safety-relevant failures: 56

### MedEval v1 Public Healthcare Seed - Clean Context Deterministic

Failure categories:
- bad_synthesis: 42
- citation_mismatch: 20
- context_overload: 67
- failed_refusal: 10
- format_failure: 7
- incomplete_answer: 18
- missing_citation: 3
- over_refusal: 1
- retrieval_rank_failure: 6
- temporal_failure: 3

Failure stages:
- citation: 10
- format: 7
- generation: 18
- refusal: 11
- synthesis: 42

Severity:
- critical: 10
- high: 42
- low: 7
- medium: 29
- Safety-relevant failures: 52

### MedEval v1 Public Healthcare Seed - Metadata-Assisted Refusal Control

Failure categories:
- bad_synthesis: 45
- citation_mismatch: 10
- context_overload: 68
- failed_refusal: 17
- incomplete_answer: 16
- missing_citation: 20
- over_refusal: 1
- retrieval_rank_failure: 6
- temporal_failure: 2

Failure stages:
- citation: 10
- generation: 16
- refusal: 18
- synthesis: 45

Severity:
- critical: 17
- high: 45
- medium: 27
- Safety-relevant failures: 62

### MedEval v1 Public Healthcare Seed - Clean Context Refusal Control

Failure categories:
- bad_synthesis: 42
- citation_mismatch: 10
- context_overload: 67
- failed_refusal: 17
- incomplete_answer: 18
- missing_citation: 20
- over_refusal: 1
- retrieval_rank_failure: 6
- temporal_failure: 2

Failure stages:
- citation: 10
- generation: 18
- refusal: 18
- synthesis: 42

Severity:
- critical: 17
- high: 42
- medium: 29
- Safety-relevant failures: 59

## Notes And Limitations

- Deterministic local comparisons are useful for pipeline debugging and regression testing.
- Refusal-aware variants may use QA metadata as a deterministic control, or oracle/control, not as a real model capability.
- Clean-context variants strip frontmatter and source metadata before deterministic answer generation.
- These reports do not claim real-world performance, clinical validation, production readiness, or external adoption.