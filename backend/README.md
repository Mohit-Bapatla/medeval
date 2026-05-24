# MedEval Backend

FastAPI service for MedEval. Batch 0 includes health/status endpoints, settings,
database wiring, Alembic setup, and a minimal test suite.

## Local Development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest
uvicorn app.main:app --reload --port 8000
```

The backend reads configuration from environment variables. A root `.env.example`
is provided for local placeholders; do not commit real secrets.
