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

## Batch 4 CLI

The backend package also installs a Typer CLI for the same local workflows:

```powershell
cd backend
.\.venv\Scripts\medeval status
.\.venv\Scripts\medeval seed-docs --path ..\datasets\sample\documents
.\.venv\Scripts\medeval seed-qa --dataset-name "MedEval HealthcareQA Sample" --path ..\datasets\sample\qa\healthcare_qa_sample.jsonl
.\.venv\Scripts\medeval run-experiment --config ..\configs\experiments\baseline_deterministic.yaml
```

The CLI uses deterministic local providers and synthetic sample data only.
