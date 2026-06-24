# MedEval v1 Benchmark Dataset

This directory contains the in-development MedEval v1 healthcare RAG benchmark
dataset scaffold plus a small seed set of real public healthcare source
documents. It is not a completed benchmark, validated clinical dataset, or
source of benchmark results.

Current Batch 7 status:

- Real public source documents: 14
- Real evidence-linked QA examples: 92
- QA split counts: 60 main evaluation, 15 hard, 17 refusal
- Example QA fixtures: 3 small schema examples kept separate from real stats
- Deterministic local baseline config: available
- Multi-config deterministic comparison configs: available
- Current deterministic seed report artifacts: available under `reports/`
- Rich failure taxonomy diagnostics: included in generated reports
- External provider comparisons: future batches
- Clinical validation: none

## Intended Contents

- `documents/`: concise Markdown summaries of public healthcare source pages,
  each with source attribution metadata.
- `qa/`: evidence-linked QA JSONL files for standard, hard, and refusal subsets.
- `metadata/docs.json`: real seed document source metadata records.
- `metadata/docs.example.json`: schema/example document metadata record.
- `metadata/labels.example.json`: example review/label metadata records.
- `metadata/taxonomy.yaml`: controlled values for source types, answer types,
  difficulties, and analysis categories.

## Source Publishers

The current seed set includes public sources from:

- CDC
- NIH/NLM MedlinePlus
- FDA
- CMS
- Medicare.gov
- HHS Office for Civil Rights
- ClinicalTrials.gov / NIH NLM

## Data Policy

Use only public, non-sensitive sources that can be redistributed or clearly
linked with license notes. Do not add PHI, private patient records, private
student data, internal clinical records, or confidential organization data.

Each real document has a `source_url`, `accessed_at` date, publisher, source
type, and licensing/access note. These notes are cautious by design: verify
source-specific reuse requirements before redistributing derived benchmark
artifacts.

The real QA files are evidence-linked benchmark-development examples. The
`.example.jsonl` files remain schema examples only. None of the QA files have
been clinically reviewed.

## QA Coverage

The current real QA files are:

- `qa/qa_eval.jsonl`: 60 main evaluation examples
- `qa/qa_hard.jsonl`: 15 harder examples, including multi-hop, comparison,
  ambiguous, temporal, and contradiction-sensitive prompts
- `qa/qa_refusal.jsonl`: 17 unsupported, out-of-scope, or patient-specific
  refusal examples

Categories represented include eligibility, deadlines, step-by-step process,
benefits and services, restrictions and exclusions, location/contact,
privacy/safety, clinical caution, multi-hop, ambiguous, unsupported,
out-of-scope, contradiction-sensitive, and temporal/versioned examples.

Each answerable QA example includes `gold_doc_ids` and `gold_evidence_spans`
with exact `start_char` and `end_char` offsets into the source Markdown
documents. Refusal examples do not require evidence spans, but they must set
`requires_refusal` and `unsupported_reason`.

These examples are for benchmark development. They are not medical advice,
clinical labels, or clinician-reviewed annotations.

## Safety And Limitations

MedEval v1 is in development. It is an evaluation dataset scaffold, not medical
advice, not diagnostic guidance, and not clinically validated. Do not use these
documents or examples to make decisions about individual patients.

## Validation

From `backend/`, run:

```bash
medeval validate-dataset --path ../datasets/medeval-v1
medeval dataset-stats --path ../datasets/medeval-v1
```

The validator checks the expected folder structure, JSON/JSONL schema, taxonomy
values, duplicate document and QA IDs, metadata references, and document paths.

## Run MedEval v1 Locally

From the repository root, start the database if needed:

```bash
docker compose up -d db
```

Then from `backend/`:

```bash
python -m alembic upgrade head
medeval validate-dataset --path ../datasets/medeval-v1
medeval dataset-stats --path ../datasets/medeval-v1
medeval seed-dataset --path ../datasets/medeval-v1 --dataset-name "MedEval v1 Public Healthcare Seed"
medeval run-experiment --config ../configs/experiments/medeval_v1_deterministic.yaml
```

The deterministic config uses the local deterministic provider only. It does
not call OpenAI, Anthropic, or any external model API.

After `run-experiment` prints an experiment ID, export local deterministic
artifacts with:

```bash
medeval export-report --experiment-id <experiment-id> --format markdown --out ../reports/medeval_v1_seed_report.md
medeval export-report --experiment-id <experiment-id> --format json --out ../reports/medeval_v1_seed_report.json
medeval export-results --experiment-id <experiment-id> --format csv --out ../reports/medeval_v1_seed_results.csv
```

These reports are local deterministic baseline artifacts for an in-development
public healthcare seed dataset. They are not clinically validated, not medical
advice, and not benchmark-complete results.

## Current Deterministic Seed Artifacts

The repository includes current deterministic local report artifacts under
`reports/`:

- `medeval_v1_seed_report.md`
- `medeval_v1_seed_report.json`
- `medeval_v1_seed_results.csv`
- `medeval_v1_comparison_report.md`
- `medeval_v1_comparison_report.json`
- `medeval_v1_comparison_results.csv`

These artifacts were generated from local Postgres-backed deterministic runs
over the 14-document, 92-QA public healthcare seed dataset. They include
heuristic rich failure diagnostics: category counts, stage counts, severity
counts, safety-relevant failure counts, legacy failure counts, and
representative failure examples with diagnostic notes.

They are not clinically validated, not medical advice, not a completed
benchmark, and not a real model leaderboard.

## Multi-Config Deterministic Comparisons

After seeding the dataset, run several deterministic variants:

```bash
medeval run-experiment --config ../configs/experiments/medeval_v1_deterministic.yaml
medeval run-experiment --config ../configs/experiments/medeval_v1_deterministic_clean_context.yaml
medeval run-experiment --config ../configs/experiments/medeval_v1_deterministic_refusal_aware.yaml
medeval run-experiment --config ../configs/experiments/medeval_v1_deterministic_top5_clean_refusal.yaml
```

Then compare completed experiment IDs:

```bash
medeval compare-runs --experiment-id <baseline-id> --experiment-id <clean-context-id> --experiment-id <refusal-aware-id> --experiment-id <clean-refusal-id> --format markdown --out ../reports/medeval_v1_comparison_report.md
medeval compare-runs --experiment-id <baseline-id> --experiment-id <clean-context-id> --experiment-id <refusal-aware-id> --experiment-id <clean-refusal-id> --format json --out ../reports/medeval_v1_comparison_report.json
medeval compare-runs --experiment-id <baseline-id> --experiment-id <clean-context-id> --experiment-id <refusal-aware-id> --experiment-id <clean-refusal-id> --format csv --out ../reports/medeval_v1_comparison_results.csv
```

The clean-context variant removes YAML frontmatter and source metadata lines
from retrieved context before deterministic answer generation. The
refusal-aware variant is a metadata-assisted deterministic refusal control that
uses QA `requires_refusal` metadata. These variants are debugging/regression
controls, not real model leaderboard claims.
