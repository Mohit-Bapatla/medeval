# Sample Datasets

Future sample datasets should be fake, synthetic, or demo-only. Do not place real
patient data, private student data, or sensitive operational data in this folder.

## Batch 1 Documents

`documents/` contains fictional healthcare opportunity and onboarding markdown
documents for local ingestion and retrieval testing. They are not real programs,
policies, clinical guidance, or benchmark evidence.

`qa/` contains fictional QA examples for local benchmark workflow development.
They are not validated benchmark results.

For a dashboard demo, seed documents, seed QA, run the deterministic sample
experiment, then open the frontend:

```powershell
python scripts/seed_sample_documents.py
python scripts/seed_sample_qa.py
python scripts/run_sample_experiment.py
```

Batch 4 also supports the CLI workflow:

```powershell
cd backend
.\.venv\Scripts\medeval seed-docs --path ..\datasets\sample\documents
.\.venv\Scripts\medeval seed-qa --dataset-name "Synthetic Healthcare Opportunity QA" --path ..\datasets\sample\qa\healthcare_qa_sample.jsonl
.\.venv\Scripts\medeval run-experiment --config ..\configs\experiments\baseline_deterministic.yaml
```

See `docs/benchmark-card.md` for the synthetic sample benchmark card. It
documents intended use, limitations, and the fact that this sample is not
validated healthcare data.
