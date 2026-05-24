# Dataset Schema

MedEval datasets will use explicit, reviewable QA examples. Batch 0 documents the
planned fields only; real schemas and migrations will come later.

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

## Data Policy

Use fake/demo/sample data in this repository. Do not commit real patient data,
private student data, or sensitive operational data.
