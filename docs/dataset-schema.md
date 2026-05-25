# Dataset Schema

MedEval stores source documents and chunks now, and will later add explicit,
reviewable QA examples for evaluation datasets.

## Batch 1 Document Fields

- `title`: document title
- `source_url`: optional source URL
- `source_type`: `healthcare_opportunity`, `volunteer_listing`,
  `onboarding_doc`, `application_instructions`, `compliance_policy`,
  `synthetic_demo`, or `unknown`
- `organization_name`: optional organization label
- `document_type`: document category
- `raw_text`: original extracted or submitted text
- `cleaned_text`: conservative cleaned text used for chunking
- `metadata_json`: non-sensitive structured metadata

## Batch 1 Chunk Fields

- `document_id`: parent document
- `chunk_index`: deterministic order within the document
- `chunk_text`: chunk content
- `token_count`: approximate whitespace token count
- `char_start` and `char_end`: offsets into cleaned text
- `embedding`: pgvector-compatible `vector(384)` in PostgreSQL
- `embedding_model`: default `deterministic-hash-embedding-384`
- `metadata_json`: non-sensitive chunk metadata

## Planned QA Example Fields

- `question`: the user-facing evaluation question
- `gold_answer`: expected answer or answer summary
- `answerability`: whether the question should be answered, refused, or marked
  insufficient evidence
- `required_evidence`: source evidence needed to justify the answer
- `category`: clinical or workflow category for analysis
- `difficulty`: coarse difficulty label for stratified reporting
- `risk_level`: expected risk level if answered incorrectly
- `reviewed_by_human`: whether a qualified reviewer has checked the example

Batch 2 implements these fields in `qa_examples`, with enum-like string
validation at the API layer.

## Evidence Links

`evidence_links` connect QA examples to expected chunks:

- `required`: needed to answer the question
- `acceptable`: can support a valid answer or citation
- `supporting`: useful context, not required for MVP recall

Sample JSONL may reference evidence by raw `chunk_id` or by
`document_file + chunk_index` after sample documents are seeded.

## Model Response Trace Fields

`model_responses` store deterministic local RAG output:

- answer text and answerability
- cited and retrieved chunk IDs
- raw structured provider output
- local latency, token estimates, and estimated cost
- provider/model names and prompt template reference

These traces support reproducibility and evaluator debugging; they are not
benchmark results by themselves.

## Human Reviews

`human_reviews` store optional local review labels for model responses:

- reviewer name and role, both optional
- correctness label: `correct`, `partially_correct`, `incorrect`, or `unsure`
- groundedness label: `grounded`, `partially_grounded`, `unsupported`, or
  `unsure`
- refusal label: `correct_refusal`, `failed_refusal`, `over_refusal`, or
  `not_applicable`
- notes and metadata

No fake human reviews are seeded. A review record does not imply clinician
review unless the reviewer role explicitly says so.

## Evaluation Metadata

Batch 4 keeps claim-level support and richer failure analysis in
`evaluation_results.metadata_json`:

- `claim_support`: deterministic claim counts, support rates, citation coverage,
  and per-claim support statuses
- `failure_analysis`: primary/secondary failure labels, failure reason, evidence
  summary, and retrieval-vs-generation flags

These fields are heuristic evaluator outputs, not validated benchmark results.

## Data Policy

Use fake/demo/sample data in this repository. Do not commit real patient data,
private student data, or sensitive operational data.
