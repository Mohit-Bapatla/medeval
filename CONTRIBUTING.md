# Contributing

Thanks for considering a contribution to MedEval. The project is early-stage
and focuses on RAG/LLM evaluation, traces, metrics, reports, and reproducible
workflows.

## Setup

```powershell
Copy-Item .env.example .env
docker compose up -d db

cd backend
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m alembic upgrade head

cd ..\frontend
npm.cmd install
```

Do not commit `.env` or any real secrets.

## Development

- Keep changes modular and explicit.
- Prefer small services and clear schemas over hidden framework magic.
- Do not add real provider calls to tests.
- Do not use real patient data or private student data.
- Use synthetic/demo data for fixtures, screenshots, and examples.
- Keep generated reports out of commits unless they are clearly labeled as
  synthetic deterministic sample artifacts.

## Validation

Backend:

```powershell
cd backend
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python -m ruff check .
.\.venv\Scripts\python -m alembic heads
```

Frontend:

```powershell
cd frontend
npm.cmd run typecheck
npm.cmd run build
```

## Pull Requests

Please include:

- a concise summary
- validation commands run
- screenshots for UI changes
- docs updates when behavior changes
- confirmation that no secrets, patient data, or private student data were added

## Data Guidance

Accepted demo data should be synthetic, clearly labeled, and safe to share in a
public repository. Do not submit real patient data, private student data, or
data copied from systems without explicit permission and governance.

## MedEval v1 Dataset Contributions

MedEval v1 dataset contributions must be conservative and auditable:

- use public healthcare sources only;
- include source URLs, publishers, access dates, and licensing/access notes;
- avoid PHI, real patient records, private student data, and private
  organization data;
- avoid protected textbooks, paywalled clinical resources, and unclear reuse
  terms;
- include exact evidence spans for QA examples;
- keep refusal cases honest about what the source does not support;
- do not add unsupported claims, fake metrics, fake review labels, or clinical
  validation language;
- run dataset validation before opening a pull request.

Public-source summaries should be concise, attributed, and suitable for
evaluation development. They should not be presented as medical advice.
