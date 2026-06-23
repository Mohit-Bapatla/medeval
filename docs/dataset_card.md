# MedEval v1 Dataset Card

## Status

MedEval v1 is currently an in-development dataset scaffold with a small seed set
of real public healthcare source documents. It is not a completed benchmark and
does not contain validated benchmark results.

Current Batch 2 contents:

- 14 concise public-document seed files
- source metadata in `datasets/medeval-v1/metadata/docs.json`
- controlled taxonomy metadata
- 3 small QA example fixtures for schema validation only
- no scaled QA benchmark set yet
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

The QA examples remain placeholders. QA expansion, evidence-span review, hard
subsets, refusal examples, and benchmark runs are future batches.

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
