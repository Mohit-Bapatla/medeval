# Metrics

MedEval will report metrics for healthcare RAG reliability. Batch 0 defines the
planned metric vocabulary but does not include validated benchmark results.

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
