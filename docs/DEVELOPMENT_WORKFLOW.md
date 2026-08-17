# Backend Development Workflow

## Table of Contents

- [Setup](#setup)
- [Commands](#commands)
- [Environment](#environment)
- [Validation](#validation)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Maintenance Checklist](#maintenance-checklist)

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8002
```

On Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8002
```

## Commands

| Command | Purpose |
| --- | --- |
| `uvicorn main:app --reload --port 8002` | Run local backend |
| `python -m py_compile main.py core/*.py routers/*.py` | Syntax check |
| `curl http://127.0.0.1:8002/api/health` | Health check |
| `sqlite3 calcvoyager.db .schema` | Inspect local SQLite schema |

## Environment

Use `backend/.env` for local overrides. The app loads this file manually before importing storage.

Important variables:

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | JWT signing secret |
| `TOKEN_EXPIRE_MINUTES` | JWT lifetime |
| `DB_PATH` | SQLite database path |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins |
| `DB_BACKEND`, `DATABASE_BACKEND`, `PROGRESS_DB` | Storage backend selector |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Backend-only Supabase credential |

## Validation

Before opening a backend PR:

```bash
cd backend
python -m py_compile main.py core/*.py routers/*.py
uvicorn main:app --reload --port 8002
```

Then confirm:

```bash
curl http://127.0.0.1:8002/api/health
```

For API changes, manually test signup/login and at least one protected route using the returned bearer token.

## Deployment

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8002
```

Production requirements:

- Strong `SECRET_KEY`.
- Narrow `ALLOWED_ORIGINS`.
- Persistent SQLite volume or Supabase configuration.
- HTTPS at the edge/proxy.
- No committed `.env`, database, or secret files.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `401 Not authenticated` | Missing/invalid bearer token | Log in and pass `Authorization: Bearer <token>` |
| CORS failure | Frontend origin missing | Update `ALLOWED_ORIGINS` |
| Supabase schema cache error | Tables missing | Run `supabase_schema.sql` |
| Supabase RLS error | RLS blocks backend key | Use service role key or update RLS policies |
| SQLite database locked | Multiple workers/processes | Use one local worker |
| Password always rejected | Wrong database or changed user row | Confirm `DB_PATH` and recreate local test user |

## Maintenance Checklist

- Keep `API_REFERENCE.md` updated with route changes.
- Keep `DATA_AND_AUTH.md` updated with schema or auth changes.
- Keep `.env.example` aligned with runtime configuration.
- Keep custom `/docs` HTML in `main.py` aligned with API changes.
- Add route tests before broadening public deployment.
