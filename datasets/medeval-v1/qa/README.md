# MedEval v1 QA Files

QA files are JSONL, one record per line. Each example should include a stable
`qa_id`, question, answer type, expected answer, difficulty, category, and either
gold evidence spans or a refusal/unsupported reason.

Recommended subsets:

- `qa_eval.jsonl`: real main evaluation examples.
- `qa_hard.jsonl`: real harder examples such as multi-hop, comparison,
  temporal, ambiguous, or contradiction-sensitive questions.
- `qa_refusal.jsonl`: real unsupported or out-of-scope examples that should
  trigger refusal behavior.
- `qa_eval.example.jsonl`: standard evidence-linked examples.
- `qa_hard.example.jsonl`: harder examples such as multi-hop, comparison,
  temporal, ambiguous, or contradiction-sensitive questions.
- `qa_refusal.example.jsonl`: unsupported or out-of-scope examples that should
  trigger refusal behavior.

Current real QA count: 230 examples across 150 main evaluation, 40 hard, and 40
refusal records. The `.example.jsonl` files remain schema examples and are not
counted as real benchmark-development QA.

Answerable examples must cite exact source text with character offsets into the
Markdown source documents. Refusal examples must set `requires_refusal: true`
and provide an `unsupported_reason`.

These files are for benchmark development. They are not medical advice,
clinically reviewed annotations, or completed benchmark results.
