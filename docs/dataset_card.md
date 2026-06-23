# MedEval v1 Dataset Card

## Status

MedEval v1 is currently a dataset scaffold, not a completed benchmark. The
repository contains example fixtures and validation code so future batches can
add real public healthcare documents, provenance metadata, evidence-linked QA
examples, hard subsets, refusal examples, and benchmark reports.

## Intended Use

MedEval is intended to evaluate healthcare RAG systems on source-grounded
question answering, retrieval, citations, refusal behavior, and failure modes.
It is for research and engineering evaluation only. It is not a medical device,
clinical decision support system, diagnostic tool, or source of medical advice.

## Data Sources

Future dataset records should use public, non-sensitive healthcare sources such
as public health guidance, patient education materials, federal or state policy,
clinical trial public records, drug/device safety notices, insurance program
materials, nonprofit program pages, or clearly marked synthetic scenarios.

Current examples are placeholders. They do not imply that real benchmark
documents have been collected.

## Annotation Design

Each QA example should include:

- a stable `qa_id`
- controlled category, difficulty, and answer type values
- expected answer text
- gold document IDs
- evidence spans with character offsets and copied span text
- refusal flags and unsupported reasons when applicable
- notes for provenance or review context

## Exclusions

Do not include PHI, private patient records, private student data, confidential
clinical records, or any non-public operational data.

## Validation

The initial filesystem validator checks structure, schema compatibility,
taxonomy-controlled values, duplicate QA IDs, label references, and document
metadata links. Passing validation means the fixture is structurally well formed;
it does not mean the dataset is clinically validated or benchmark-grade.

