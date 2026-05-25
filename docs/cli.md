# MedEval CLI

The `medeval` CLI supports deterministic local development workflows. It does
not call external model providers and does not require OpenAI or Anthropic keys.

## Install

```powershell
cd backend
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

## Commands

```powershell
.\.venv\Scripts\medeval status
.\.venv\Scripts\medeval seed-docs --path ..\datasets\sample\documents
.\.venv\Scripts\medeval seed-qa --dataset-name "MedEval HealthcareQA Sample" --path ..\datasets\sample\qa\healthcare_qa_sample.jsonl
.\.venv\Scripts\medeval run-experiment --config ..\configs\experiments\baseline_deterministic.yaml
.\.venv\Scripts\medeval export-report --experiment-id <experiment-id> --format markdown --out ..\reports\example_report.md
.\.venv\Scripts\medeval export-report --experiment-id <experiment-id> --format json --out ..\reports\example_report.json
.\.venv\Scripts\medeval export-results --experiment-id <experiment-id> --format csv --out ..\reports\results.csv
```

## Notes

- The CLI uses the configured `DATABASE_URL`.
- Run the sample commands from `backend/` so the relative paths resolve as shown.
- Sample configs use deterministic local providers and synthetic data.
- Exported reports include limitations and are not validated benchmark results.
- Do not use the CLI to write real patient data, private student data, secrets,
  or real provider keys into the repository.
