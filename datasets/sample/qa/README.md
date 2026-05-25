# Synthetic QA Sample

`healthcare_qa_sample.jsonl` contains fictional QA examples for local MedEval
development. The questions are based on the synthetic markdown documents in
`datasets/sample/documents/`.

These examples are not benchmark results, clinical validation, user evidence, or
real healthcare data. Evidence references use `document_file` plus `chunk_index`
so they can resolve after sample documents are seeded, chunked, and embedded.
