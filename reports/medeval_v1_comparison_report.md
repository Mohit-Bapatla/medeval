# MedEval v1 Deterministic Comparison Report

Generated: 2026-06-24T05:48:01.492107+00:00

## Disclaimer

This report is computed from a local deterministic run over the connected database, including synthetic samples or the in-development MedEval v1 public healthcare seed dataset. It is not a validated benchmark, clinical validation, medical advice, healthcare validation, production-use evidence, or an external adoption claim.

This comparison is a deterministic local debugging/regression workflow for an in-development public healthcare seed dataset. It is not clinical validation, medical advice, or a validated leaderboard.

## Compared Experiments

| Experiment | ID | Status | Model | top_k | Examples |
| --- | --- | --- | --- | ---: | ---: |
| MedEval v1 Public Healthcare Seed - Deterministic Baseline | 11eede9a | completed | deterministic-extractive-answer-v1 | 5 | 230 |
| MedEval v1 Public Healthcare Seed - Clean Context Deterministic | 47162b10 | completed | deterministic-extractive-answer-v1-clean-context | 5 | 230 |
| MedEval v1 Public Healthcare Seed - Metadata-Assisted Refusal Control | cfd9bd4a | completed | deterministic-extractive-answer-v1-refusal-oracle | 5 | 230 |
| MedEval v1 Public Healthcare Seed - Clean Context Refusal Control | 59d4ee82 | completed | deterministic-extractive-answer-v1-clean-refusal-oracle | 5 | 230 |

## Aggregate Metrics

| Experiment | Correctness | Groundedness | Citation Precision | Citation Recall | Retrieval Precision | Retrieval Recall | Refusal Accuracy | Hallucination Rate | Avg Latency | Cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| MedEval v1 Public Healthcare Seed - Deterministic Baseline | 0.295 | 0.996 | 0.743 | 0.847 | 0.186 | 0.944 | 0.861 | 0.139 | 0.000 | 0.000 |
| MedEval v1 Public Healthcare Seed - Clean Context Deterministic | 0.335 | 0.991 | 0.739 | 0.843 | 0.186 | 0.944 | 0.861 | 0.139 | 0.000 | 0.000 |
| MedEval v1 Public Healthcare Seed - Metadata-Assisted Refusal Control | 0.430 | 0.822 | 0.865 | 0.847 | 0.186 | 0.944 | 0.996 | 0.178 | 0.009 | 0.000 |
| MedEval v1 Public Healthcare Seed - Clean Context Refusal Control | 0.465 | 0.817 | 0.856 | 0.843 | 0.186 | 0.944 | 0.991 | 0.183 | 0.004 | 0.000 |

## Deltas Vs Baseline

| Experiment | Correctness Δ | Groundedness Δ | Citation Recall Δ | Retrieval Recall Δ | Refusal Accuracy Δ | Hallucination Rate Δ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| MedEval v1 Public Healthcare Seed - Deterministic Baseline | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| MedEval v1 Public Healthcare Seed - Clean Context Deterministic | +0.039 | -0.004 | -0.004 | +0.000 | +0.000 | +0.000 |
| MedEval v1 Public Healthcare Seed - Metadata-Assisted Refusal Control | +0.135 | -0.174 | +0.000 | +0.000 | +0.135 | +0.039 |
| MedEval v1 Public Healthcare Seed - Clean Context Refusal Control | +0.170 | -0.178 | -0.004 | +0.000 | +0.130 | +0.043 |

## Failure Type Counts

### MedEval v1 Public Healthcare Seed - Deterministic Baseline

- bad_citation: 27
- evaluator_insufficient_data: 9
- failed_to_refuse: 31
- missing_citation: 10
- none: 14
- over_refusal: 1
- partial_answer: 40
- retrieval_miss: 2
- wrong_answer: 96

### MedEval v1 Public Healthcare Seed - Clean Context Deterministic

- bad_citation: 30
- evaluator_insufficient_data: 10
- failed_to_refuse: 30
- missing_citation: 10
- none: 16
- over_refusal: 2
- partial_answer: 48
- retrieval_miss: 2
- wrong_answer: 82

### MedEval v1 Public Healthcare Seed - Metadata-Assisted Refusal Control

- bad_citation: 27
- failed_to_refuse: 40
- missing_citation: 10
- none: 14
- over_refusal: 1
- partial_answer: 40
- retrieval_miss: 2
- wrong_answer: 96

### MedEval v1 Public Healthcare Seed - Clean Context Refusal Control

- bad_citation: 30
- failed_to_refuse: 40
- missing_citation: 10
- none: 16
- over_refusal: 2
- partial_answer: 48
- retrieval_miss: 2
- wrong_answer: 82

## Rich Failure Diagnostics

### MedEval v1 Public Healthcare Seed - Deterministic Baseline

Failure categories:
- bad_synthesis: 96
- citation_mismatch: 70
- context_overload: 157
- failed_refusal: 31
- format_failure: 9
- incomplete_answer: 40
- missing_citation: 13
- over_answering: 1
- over_refusal: 1
- retrieval_miss: 3
- retrieval_rank_failure: 20
- temporal_failure: 12

Failure stages:
- citation: 37
- format: 9
- generation: 40
- refusal: 32
- retrieval: 2
- synthesis: 96

Severity:
- critical: 31
- high: 99
- low: 9
- medium: 77
- Safety-relevant failures: 127

### MedEval v1 Public Healthcare Seed - Clean Context Deterministic

Failure categories:
- bad_synthesis: 82
- citation_mismatch: 72
- context_overload: 153
- failed_refusal: 30
- format_failure: 10
- incomplete_answer: 48
- missing_citation: 14
- over_answering: 1
- over_refusal: 2
- retrieval_miss: 3
- retrieval_rank_failure: 20
- temporal_failure: 12

Failure stages:
- citation: 40
- format: 10
- generation: 48
- refusal: 32
- retrieval: 2
- synthesis: 82

Severity:
- critical: 30
- high: 85
- low: 10
- medium: 89
- Safety-relevant failures: 112

### MedEval v1 Public Healthcare Seed - Metadata-Assisted Refusal Control

Failure categories:
- bad_synthesis: 96
- citation_mismatch: 39
- context_overload: 157
- failed_refusal: 40
- incomplete_answer: 40
- missing_citation: 53
- over_refusal: 1
- retrieval_miss: 3
- retrieval_rank_failure: 20
- temporal_failure: 10

Failure stages:
- citation: 37
- generation: 40
- refusal: 41
- retrieval: 2
- synthesis: 96

Severity:
- critical: 40
- high: 99
- medium: 77
- Safety-relevant failures: 136

### MedEval v1 Public Healthcare Seed - Clean Context Refusal Control

Failure categories:
- bad_synthesis: 82
- citation_mismatch: 42
- context_overload: 153
- failed_refusal: 40
- incomplete_answer: 48
- missing_citation: 54
- over_refusal: 2
- retrieval_miss: 3
- retrieval_rank_failure: 20
- temporal_failure: 10

Failure stages:
- citation: 40
- generation: 48
- refusal: 42
- retrieval: 2
- synthesis: 82

Severity:
- critical: 40
- high: 85
- medium: 89
- Safety-relevant failures: 122

## Notes And Limitations

- Deterministic local comparisons are useful for pipeline debugging and regression testing.
- Refusal-aware variants may use QA metadata as a deterministic control, or oracle/control, not as a real model capability.
- Clean-context variants strip frontmatter and source metadata before deterministic answer generation.
- These reports do not claim real-world performance, clinical validation, production readiness, or external adoption.