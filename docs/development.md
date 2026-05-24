# Development

## Safety Rules

- Do not commit `.env` files or real API keys.
- Use `.env.example` for placeholders only.
- Do not commit real patient data, private student data, or fabricated benchmark
  results.
- Keep examples fake, synthetic, or clearly marked as demo-only.

## Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest
ruff check .
uvicorn app.main:app --reload --port 8000
```

## Frontend

```powershell
cd frontend
npm install
npm run typecheck
npm run dev
```

## Database

```powershell
Copy-Item .env.example .env
docker compose up -d db
cd backend
alembic upgrade head
```

The first migration enables the PostgreSQL `vector` extension for pgvector.
