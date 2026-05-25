# Scripts

Utility scripts for local development and maintenance can be added here in later
batches.

## Seed Synthetic Documents

`seed_sample_documents.py` loads the fictional markdown files from
`datasets/sample/documents/`, chunks them, embeds them with the deterministic
local provider, and stores them in the configured database.

Run only after the database is available and migrations have been applied:

```powershell
python scripts/seed_sample_documents.py
```

## Seed Synthetic QA

`seed_sample_qa.py` creates a synthetic QA dataset and imports
`datasets/sample/qa/healthcare_qa_sample.jsonl`. Seed documents first so evidence
references can resolve.

```powershell
python scripts/seed_sample_qa.py
```

## Run Synthetic Experiment

`run_sample_experiment.py` runs a synchronous deterministic local experiment over
the seeded synthetic QA dataset. The output is a local development smoke summary,
not a benchmark result.

```powershell
python scripts/run_sample_experiment.py
```
