# MedEval v1 Benchmark Dataset

This directory is the scaffold for the future MedEval v1 healthcare RAG
benchmark dataset. It currently contains schemas, controlled taxonomy metadata,
and small example fixtures only. It does not contain a collected benchmark,
validated clinical dataset, or benchmark results.

## Intended Contents

- `documents/`: future public-source healthcare documents in Markdown or text.
- `qa/`: evidence-linked QA JSONL files for standard, hard, and refusal subsets.
- `metadata/docs.example.json`: example document source metadata records.
- `metadata/labels.example.json`: example review/label metadata records.
- `metadata/taxonomy.yaml`: controlled values for source types, answer types,
  difficulties, and analysis categories.

## Data Policy

Use only public, non-sensitive sources that can be redistributed or clearly
linked with license notes. Do not add PHI, private patient records, private
student data, internal clinical records, or confidential organization data.

The examples in this scaffold are placeholders. Replace them in later batches
with real public-source documents and evidence spans only after source metadata,
license notes, and provenance have been reviewed.

## Validation

From `backend/`, run:

```bash
medeval validate-dataset --path ../datasets/medeval-v1
medeval dataset-stats --path ../datasets/medeval-v1
```

The validator checks the expected folder structure, JSON/JSONL schema, taxonomy
values, duplicate QA IDs, metadata references, and placeholder document paths.

