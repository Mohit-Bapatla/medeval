# MedEval v1 Dataset Card

## Status

MedEval v1 is currently an in-development dataset scaffold with a small seed set
of real public healthcare source documents. It is not a completed benchmark and
does not contain validated benchmark results.

Current Batch 5 contents:

- 14 concise public-document seed files
- source metadata in `datasets/medeval-v1/metadata/docs.json`
- controlled taxonomy metadata
- 92 real evidence-linked QA examples
- 3 small QA example fixtures kept separate from real dataset stats
- deterministic local baseline config and seed command support
- deterministic local comparison configs and `compare-runs` reporting
- no clinical validation

## Intended Use

MedEval is intended to evaluate healthcare RAG systems on source-grounded
question answering, retrieval, citations, refusal behavior, and failure modes.
It is for research and engineering evaluation only. It is not a medical device,
clinical decision support system, diagnostic tool, or source of medical advice.

## Data Sources

The current seed set uses public, non-sensitive healthcare sources from CDC,
NIH/NLM MedlinePlus, FDA, CMS, Medicare.gov, HHS Office for Civil Rights, and
ClinicalTrials.gov / NIH NLM.

Current source categories represented:

- public health guidance
- patient education
- drug/device safety
- insurance program information
- federal privacy policy
- clinical trial registry information

The Markdown files are concise attribution summaries, not full scraped copies of
the source pages. Each record includes source URL, publisher, access date,
source type, domain, and licensing/access notes. Source-specific reuse
requirements should be checked again before any redistributed release artifact.

The real QA examples now cover direct extraction, lists, eligibility,
restrictions, timing, clinical caution, privacy/safety, Medicare/CMS policy,
drug safety, clinical trial eligibility, multi-hop/comparison questions,
ambiguous prompts, and unsupported/refusal behavior. Deterministic local
comparison reports can compare config variants for debugging and regression
testing. External-provider benchmark runs are future batches.

Current real QA split counts:

- `qa_eval.jsonl`: 60
- `qa_hard.jsonl`: 15
- `qa_refusal.jsonl`: 17
- total real QA examples: 92

## Annotation Design

Each QA example should include:

- a stable `qa_id`
- controlled category, difficulty, and answer type values
- expected answer text
- gold document IDs
- evidence spans with character offsets and copied span text
- refusal flags and unsupported reasons when applicable
- notes for provenance or review context

For answerable examples, `gold_evidence_spans` contain exact text copied from a
source Markdown document plus character offsets into that document. The
validator checks that each evidence span text appears in the referenced
document and that `start_char`/`end_char` match the copied text exactly.

For refusal examples, `requires_refusal` is true, `unsupported_reason` is set,
and gold evidence spans are intentionally empty. These examples test unsupported
requests, patient-specific medical advice, privacy-sensitive requests,
completed-trial limitations, and insufficient user information.

## Exclusions

Do not include PHI, private patient records, private student data, confidential
clinical records, or any non-public operational data.

## Validation

The initial filesystem validator checks structure, schema compatibility,
taxonomy-controlled values, duplicate QA IDs, label references, and document
metadata links. Passing validation means the fixture is structurally well formed;
it does not mean the dataset is clinically validated or benchmark-grade.

## Local Run Workflow

MedEval v1 can be seeded into the backend pipeline with:

```bash
cd backend
python -m alembic upgrade head
medeval validate-dataset --path ../datasets/medeval-v1
medeval dataset-stats --path ../datasets/medeval-v1
medeval seed-dataset --path ../datasets/medeval-v1 --dataset-name "MedEval v1 Public Healthcare Seed"
medeval run-experiment --config ../configs/experiments/medeval_v1_deterministic.yaml
```

Then export local deterministic reports with `medeval export-report` and
`medeval export-results` using the experiment ID printed by `run-experiment`.
The deterministic baseline is an in-development public healthcare seed run. It
does not use external model APIs and does not establish clinical validation,
medical advice quality, production readiness, or benchmark completeness.

## Multi-Config Deterministic Comparisons

The repository includes deterministic config variants for top-k retrieval,
cleaned retrieved context, and a metadata-assisted refusal control. Compare
completed runs with:

```bash
medeval compare-runs --experiment-id <baseline-id> --experiment-id <variant-id> --format markdown --out ../reports/medeval_v1_comparison_report.md
```

JSON and CSV comparison exports are also supported. These comparisons are
debugging/regression artifacts for an in-development public healthcare seed
dataset. The refusal-aware variant is explicitly metadata-assisted and should be
interpreted as a deterministic control, not a real model capability or validated
leaderboard result.
