# Metric Definitions

MedEval distinguishes implemented demo metrics from planned MedEval v1 benchmark
metrics. Current deterministic metrics are useful for local development and
debugging, but they are not validated clinical or benchmark claims.

## Retrieval

- `recall@k`: planned MedEval v1 metric; share of required gold evidence found
  in the top `k` retrieved results.
- `precision@k`: planned MedEval v1 metric; share of the top `k` retrieved
  results that are relevant.
- `MRR`: planned MedEval v1 metric; reciprocal rank of the first relevant
  result, averaged across examples.
- `nDCG`: planned MedEval v1 metric; ranking quality with graded relevance.
- `gold evidence coverage`: planned MedEval v1 metric; share of cited gold
  evidence spans covered by retrieved context.

## Generation

- `correctness`: partially implemented with deterministic local heuristics;
  planned to become evidence-linked benchmark scoring.
- `completeness`: planned MedEval v1 metric; whether all required answer parts
  are included.
- `groundedness`: partially implemented with deterministic citation heuristics;
  planned to become claim-level support scoring.
- `unsupported claim rate`: partially implemented as heuristic metadata; planned
  for claim-level benchmark reporting.
- `contradiction rate`: planned MedEval v1 metric; share of answers that
  contradict gold evidence or source constraints.
- `rich failure categories`: partially implemented as deterministic diagnostic
  metadata. These counts describe heuristic failure labels such as
  `bad_synthesis`, `unsupported_claim`, and `incomplete_answer`; they are not
  clinical adjudication.

## Citation

- `citation precision`: partially implemented with deterministic chunk-level
  checks; planned for evidence-span and claim-level support.
- `citation recall`: partially implemented with deterministic chunk-level
  checks; planned for gold evidence-span recall.
- `claim-level support`: planned MedEval v1 metric; share of answer claims that
  are supported by cited evidence.
- `citation mismatch rate`: planned MedEval v1 metric; citations that do not
  support the associated claim.
- `missing citation rate`: planned MedEval v1 metric; answer claims needing
  citations that lack them.

## Refusal And Safety

- `refusal accuracy`: partially implemented with deterministic answerability
  checks; planned for unsupported and safety-sensitive subsets.
- `failed refusal rate`: planned MedEval v1 metric; unsupported or unsafe
  examples that receive an answer.
- `over-refusal rate`: planned MedEval v1 metric; answerable examples that are
  incorrectly refused.
- `unsafe compliance rate`: planned MedEval v1 metric; unsafe requests that are
  complied with.
- `ambiguity handling rate`: planned MedEval v1 metric; ambiguous examples that
  are clarified, scoped, or refused appropriately.

## Operational

- `latency`: currently recorded for local traces; planned for benchmark reports.
- `p50/p95 latency`: planned MedEval v1 report statistic.
- `cost`: currently estimated for local deterministic traces where available;
  planned for provider-based benchmark reporting in later batches.
- `throughput`: planned MedEval v1 operational metric.
- `pipeline failure rate`: planned MedEval v1 metric for ingestion, retrieval,
  generation, evaluation, and export failures.

## Failure Diagnostics

Reports now include legacy `failure_type` counts and rich failure diagnostics:

- `rich_failure_category_counts`: counts across the 15-category MedEval v1
  diagnostic taxonomy.
- `failure_stage_counts`: primary category stages such as retrieval, generation,
  citation, refusal, synthesis, and format.
- `failure_severity_counts`: maximum default severity per response.
- `safety_relevant_failure_count`: responses with at least one safety-relevant
  diagnostic category.

These are deterministic local diagnostics for in-development analysis, not
validated healthcare quality or safety metrics.
