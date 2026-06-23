# MedEval v1 Benchmark Dataset

This directory contains the in-development MedEval v1 healthcare RAG benchmark
dataset scaffold plus a small seed set of real public healthcare source
documents. It is not a completed benchmark, validated clinical dataset, or
source of benchmark results.

Current Batch 2 status:

- Real public source documents: 14
- Example QA fixtures: 3 small schema examples only
- Scaled QA expansion: upcoming in Batch 3
- Benchmark runs and reports: future batches
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

The QA files remain examples only. They are not a scaled benchmark set and have
not been clinically reviewed.

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
