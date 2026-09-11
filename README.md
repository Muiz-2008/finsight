# FinSight

Financial analytics, portfolio intelligence, and risk platform.

> **Status: early development.** This README will grow into the full project
> writeup (architecture, ERD, algorithms, security, engineering challenges)
> as milestones land. Right now it documents what exists: a running API
> skeleton.

## Running the backend locally

Requires Python 3.12+.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # then set a real SECRET_KEY
uvicorn app.main:app --reload
```

Check it's alive:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/health/db   # requires Postgres running
```

## Running with Docker

Requires Docker Desktop.

```bash
cp backend/.env.example backend/.env   # then set a real SECRET_KEY
docker compose up --build
```

## Tests

```bash
cd backend
source .venv/bin/activate
pytest
ruff check .
```
