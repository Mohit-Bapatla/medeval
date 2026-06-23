# MedEval v1 QA Files

QA files are JSONL, one record per line. Each example should include a stable
`qa_id`, question, answer type, expected answer, difficulty, category, and either
gold evidence spans or a refusal/unsupported reason.

Recommended subsets:

- `qa_eval.example.jsonl`: standard evidence-linked examples.
- `qa_hard.example.jsonl`: harder examples such as multi-hop, comparison,
  temporal, ambiguous, or contradiction-sensitive questions.
- `qa_refusal.example.jsonl`: unsupported or out-of-scope examples that should
  trigger refusal behavior.

These files are examples only. They are not benchmark-grade labels.

