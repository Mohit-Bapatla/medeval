# Metrics

MedEval will report metrics for healthcare RAG reliability. The current code
supports retrieval data needed for future metrics, but it does not include
validated benchmark results.

## Planned Metrics

- Correctness: whether the answer matches the expected answer for answerable
  questions.
- Groundedness: whether claims are supported by retrieved evidence.
- Hallucination rate: share of answers containing unsupported or fabricated
  claims.
- Refusal accuracy: whether the system refuses or escalates when the question is
  unanswerable or insufficiently supported.
- Citation precision: share of cited sources that actually support the answer.
- Citation recall: share of required evidence that appears in the citations.
- Retrieval recall@k: share of required evidence retrieved within the top `k`
  results.
- Retrieval precision@k: share of top `k` retrieved results that are relevant.
- Latency: elapsed time for retrieval, generation, evaluation, and total run.
- Cost: estimated provider and infrastructure cost for an experiment.
- Failure categories: labels for issues such as missing evidence, wrong answer,
  unsupported citation, unsafe refusal, or retrieval miss.

Batch 1 retrieval similarity scores are local development retrieval scores, not
validated benchmark metrics.

## Batch 2 MVP Evaluator

Batch 2 stores deterministic heuristic evaluation results:

- Retrieval recall: required evidence chunks retrieved divided by required
  evidence chunks.
- Retrieval precision: required or acceptable retrieved chunks divided by all
  retrieved chunks.
- Citation recall: required evidence chunks cited divided by required evidence
  chunks.
- Citation precision: cited chunks that are required or acceptable divided by
  all cited chunks.
- Refusal score: deterministic pass/fail for answerable versus unanswerable
  examples.
- Correctness: simple token-overlap heuristic for answerable examples.
- Groundedness: simple citation validity heuristic.
- Hallucination flag: deterministic flag for failed refusals, missing citations,
  or invalid citations.

If a metric denominator is unavailable, the metric is stored as `null` rather
than forcing a fake zero. Overall score is a transparent weighted MVP score over
available components and is not benchmark-grade.
