# MedEval v1: Public-Document Healthcare RAG Evaluation Seed Benchmark

## Executive Summary

MedEval v1 is an in-development public-document healthcare RAG evaluation seed
benchmark. It currently combines 25 public healthcare source documents, 230
exact-evidence QA examples, deterministic local experiment runs, rich failure
taxonomy diagnostics, reproducible report artifacts, and 50 completed manual
self-review calibration labels on high-priority failures.

The goal is to evaluate whether a RAG system answers healthcare-adjacent
questions with grounded citations, refuses unsupported requests, retrieves the
right evidence, and exposes traceable failure modes. The current deterministic
provider is for reproducibility and pipeline testing. It is not a real model
leaderboard, not clinical validation, not medical advice, and not clinician
review.

## What MedEval Evaluates

MedEval evaluates a full RAG reliability loop:

- document ingestion, cleaning, chunking, and embedding;
- evidence-linked QA examples;
- retrieval traces and cited chunks;
- generated answers and refusal behavior;
- correctness, groundedness, citation, retrieval, latency, and cost metrics;
- claim-level citation support heuristics;
- legacy failure types plus a richer 15-category failure taxonomy;
- manual review calibration against automated diagnostics.

The platform is designed for inspection and reproducibility. Every response can
be traced back to the question, gold answer, retrieved chunks, cited chunks,
automated scores, failure categories, and optional manual-review records.

## Dataset Composition

Current MedEval v1 dataset status:

- 25 public healthcare source documents;
- 230 exact-evidence QA examples;
- 190 answerable examples;
- 40 refusal / unanswerable examples;
- no PHI, no real patient records, no private student data;
- concise public-source attribution summaries for evaluation development.

The dataset is still in development. It is a seed benchmark artifact, not a
completed clinical benchmark.

## Document Sources And Source Types

The checked-in source documents are concise Markdown summaries derived from
stable public healthcare pages. Sources include CDC, NIH/NLM MedlinePlus, FDA,
CMS/Medicare, Medicaid.gov, HHS, and ClinicalTrials.gov.

Source-type distribution:

| Source type | Documents |
| --- | ---: |
| public_health_guidance | 9 |
| patient_education | 4 |
| insurance_program | 4 |
| drug_device_safety | 3 |
| federal_policy | 3 |
| clinical_trial | 2 |

Each document includes metadata such as `doc_id`, title, publisher, source URL,
access date, source type, domain, difficulty, document path, and licensing or
access notes. Reuse requirements should still be verified before redistribution
outside this repository context.

## QA Split Breakdown

| Split | Examples | Purpose |
| --- | ---: | --- |
| `qa_eval.jsonl` | 150 | Main evaluation examples |
| `qa_hard.jsonl` | 40 | Harder multi-hop, caution, temporal, and edge cases |
| `qa_refusal.jsonl` | 40 | Unsupported, unsafe, private, or out-of-scope requests |

Category coverage includes clinical cautions, benefits and services,
privacy/safety, restrictions and exclusions, eligibility, multi-hop questions,
temporal/versioned questions, ambiguous questions, unsupported questions, and
other healthcare-adjacent RAG behaviors.

## Evidence-Linking Methodology

Each QA example includes exact gold evidence spans linked to source Markdown.
The dataset validator checks that evidence snippets still match the source
documents, preventing silent drift when documents or QA examples change.

The evidence-linking workflow is intentionally conservative:

- gold answers are grounded in source text;
- refusal examples identify why the source should not be used to answer;
- QA files are split into eval, hard, and refusal sets;
- example-only fixture files are ignored by benchmark validation;
- metadata tracks answer type, difficulty, category, and refusal requirements.

## Deterministic Baseline Setup

The committed deterministic baseline uses:

- dataset: `MedEval v1 Public Healthcare Seed`;
- model provider: `deterministic_local`;
- model name: `deterministic-extractive-answer-v1`;
- embedding model: `deterministic-hash-embedding-384`;
- retrieval strategy: vector similarity;
- `top_k=5`;
- no external model API calls;
- no paid API keys.

This provider is deliberately deterministic so the pipeline, reports, and
failure diagnostics can be reproduced locally. It is not intended to represent
state-of-the-art model quality.

## Multi-Config Comparison Workflow

The repository includes a four-config deterministic comparison workflow:

1. baseline deterministic;
2. clean-context deterministic;
3. metadata-assisted refusal control;
4. clean-context refusal control.

The refusal-aware variants are labeled as controls. They may use QA metadata as
an oracle-like deterministic control and should not be interpreted as real model
capability.

## Metrics Tracked

MedEval tracks:

- average correctness;
- average groundedness;
- citation precision;
- citation recall;
- retrieval precision;
- retrieval recall;
- refusal accuracy;
- hallucination rate;
- claim count and claim support rate;
- latency and estimated cost when available;
- failure type and rich failure taxonomy distributions.

The baseline deterministic run over 230 examples produced:

| Metric | Value |
| --- | ---: |
| Avg correctness | 0.295 |
| Avg groundedness | 0.996 |
| Citation precision | 0.743 |
| Citation recall | 0.847 |
| Retrieval precision | 0.186 |
| Retrieval recall | 0.944 |
| Refusal accuracy | 0.861 |
| Hallucination rate | 0.139 |

These are deterministic local pipeline metrics, not validated model benchmark
scores.

## Rich Failure Taxonomy

MedEval stores both legacy `failure_type` values and rich taxonomy diagnostics.
The rich taxonomy currently includes 15 categories:

- `retrieval_miss`
- `retrieval_rank_failure`
- `context_overload`
- `unsupported_claim`
- `citation_mismatch`
- `missing_citation`
- `incomplete_answer`
- `over_answering`
- `failed_refusal`
- `over_refusal`
- `ambiguity_failure`
- `temporal_failure`
- `contradiction`
- `bad_synthesis`
- `format_failure`

Each category has a stage, default severity, and safety-relevance flag. Reports
include category counts, stage counts, severity counts, safety-relevant failure
counts, and representative examples.

## Reproducibility Workflow

The repository includes a reproducibility smoke workflow:

```bash
make medeval-v1-smoke
```

The workflow starts Postgres, applies migrations, validates the dataset, prints
dataset stats, seeds MedEval v1, runs deterministic configs, exports reports,
and checks report artifacts.

To validate checked-in reports without regenerating them:

```bash
make medeval-v1-check-reports
```

To validate the dataset only:

```bash
make medeval-v1-validate
```

## Manual Review And Calibration Workflow

MedEval v1 includes a manual review workflow for calibrating automated
diagnostics. The workflow supports:

- exporting full review queues;
- exporting curated review packets with failure-priority, random, or balanced
  selection;
- validating completed packet JSON;
- importing completed review records;
- tracking review progress;
- exporting Markdown, JSON, and CSV calibration summaries;
- reviewing responses in the dashboard.

Manual review records are workflow artifacts for calibration. They are not
clinical validation, not medical advice, and not clinician review unless an
actual clinician reviewer performed the review and the record says so.

## Manual Review Summary

The current committed calibration artifacts contain 50 completed manual
self-review calibration labels on high-priority deterministic baseline failures.
That is 21.7% of 230 baseline responses.

Average self-review scores:

| Field | Average |
| --- | ---: |
| answer_correctness | 1.00 |
| groundedness | 1.96 |
| citation_quality | 1.00 |
| refusal_safety | 1.76 |
| confidence | 4.64 |

Common reviewer-selected failure categories:

| Failure category | Count |
| --- | ---: |
| citation_mismatch | 33 |
| failed_refusal | 31 |
| bad_synthesis | 16 |
| context_overload | 10 |
| retrieval_rank_failure | 6 |
| retrieval_miss | 3 |
| missing_citation | 3 |
| temporal_failure | 3 |
| over_answering | 1 |
| over_refusal | 1 |

These labels are self-reviewed calibration labels from the repo owner workflow.
They are useful for checking whether automated diagnostics align with manual
judgment on selected high-priority failures. They are not independent external
review, clinician review, or human-validated clinical benchmark evidence.

## Key Findings From The Deterministic Baseline

- The deterministic retriever often finds relevant source material
  (`retrieval_recall=0.944`), but retrieval precision is low because top-k
  contexts include many non-required chunks.
- Groundedness is high under the heuristic evaluator, but manual self-review of
  high-priority failures identified many citation mismatches and poor answer
  quality, showing why reviewer calibration matters.
- Refusal behavior is a major failure area in the deterministic baseline:
  automated diagnostics found 31 `failed_refusal` cases, and manual self-review
  selected `failed_refusal` 31 times.
- The rich taxonomy makes the failure surface more interpretable than a single
  aggregate score: failures cluster around citation mismatch, bad synthesis,
  context overload, refusal handling, and retrieval ranking.
- The multi-config comparison is useful for regression testing and debugging,
  not for public model ranking.

## Known Limitations

- MedEval v1 is still in development.
- The deterministic provider is not a real LLM.
- The evaluator is heuristic and not clinically validated.
- The dataset is a seed set, not a full-scale benchmark.
- Public-source documents are concise attribution summaries, not full scraped
  clinical resources.
- Manual labels are self-reviewed calibration labels, not independent review.
- No clinician review has been claimed.
- No real patient data or PHI is included.
- Results should not be used for medical decisions.

## What Not To Infer

Do not infer that MedEval v1 is:

- clinically validated;
- doctor-approved;
- medical advice;
- production-ready;
- externally adopted;
- a state-of-the-art leaderboard;
- a completed healthcare benchmark;
- a human-validated or clinician-validated clinical benchmark.

The current artifacts demonstrate evaluation infrastructure, reproducibility,
failure analysis, and honest benchmark development practices.

## How To Reproduce

From the repository root:

```bash
docker compose up -d db
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
medeval validate-dataset --path ../datasets/medeval-v1
medeval dataset-stats --path ../datasets/medeval-v1
medeval seed-dataset --path ../datasets/medeval-v1 --dataset-name "MedEval v1 Public Healthcare Seed"
medeval run-experiment --config ../configs/experiments/medeval_v1_deterministic.yaml
```

From the repository root, run the full deterministic artifact loop:

```bash
make medeval-v1-smoke
```

Review checked-in artifacts under `reports/`, especially:

- `reports/medeval_v1_seed_report.md`
- `reports/medeval_v1_comparison_report.md`
- `reports/medeval_v1_manual_review_summary.md`
- `reports/examples/medeval_v1_review_packet_50.completed.json`

## Future Work

- Expand public-document coverage and QA diversity.
- Add independent reviewer workflows and adjudication.
- Add clinician review only if actual clinician reviewers participate.
- Improve retrieval precision and reranking experiments.
- Add real provider adapters while preserving deterministic local tests.
- Add stronger evaluator methods and LLM-as-judge experiments with clear
  caveats.
- Continue packaging reproducible benchmark releases without overclaiming
  clinical validity.
