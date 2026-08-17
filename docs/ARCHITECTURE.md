# Backend Architecture

## Table of Contents

- [Overview](#overview)
- [Application Lifecycle](#application-lifecycle)
- [Routing Model](#routing-model)
- [Storage Abstraction](#storage-abstraction)
- [Error Handling](#error-handling)
- [CORS and Docs](#cors-and-docs)
- [Known Risks](#known-risks)

## Overview

The backend is a small Starlette service. It avoids heavy frameworks such as SQLAlchemy and Pydantic; request parsing and validation are done manually in route handlers.

```text
main.py
  -> load .env
  -> init_storage()
  -> mount routers
  -> CORS middleware

routers/*
  -> parse JSON
  -> authenticate when needed
  -> validate required fields
  -> call core/storage.py

core/storage.py
  -> SQLite via core/db.py
  -> or Supabase client when configured
```

## Application Lifecycle

`main.py` uses a Starlette lifespan handler:

1. Load `.env` manually from `backend/.env` if present.
2. Import routers and storage.
3. On startup, call `init_storage()`.
4. If SQLite is active, create tables through `db.init_db()`.
5. If Supabase is active, assume `supabase_schema.sql` has already been applied.

## Routing Model

Routes are mounted by API area:

| Mount | Router file |
| --- | --- |
| `/api/auth` | `routers/auth.py` |
| `/api/progress` | `routers/progress.py` |
| `/api/bookmarks` | `routers/bookmarks.py` |
| `/api/quiz` | `routers/quiz.py` |
| `/api/solver` | `routers/solver_proxy.py` |

Each router returns `JSONResponse` directly and uses `core.auth_utils.err()` for common error payloads.

## Storage Abstraction

`core/storage.py` chooses the backend at import time:

- SQLite when Supabase is not configured.
- Supabase when `DB_BACKEND=supabase`, `DATABASE_BACKEND=supabase`, `PROGRESS_DB=supabase`, or both `SUPABASE_URL` and a Supabase key are present.

SQLite operations use `asyncio.to_thread` wrappers around stdlib `sqlite3`, keeping route handlers async while avoiding an additional async database dependency.

## Error Handling

Current behavior:

- Invalid JSON returns `400`.
- Missing auth returns `401`.
- Duplicate usernames return `409`.
- Supabase schema/RLS errors receive clearer messages in auth routes.
- Some storage exceptions may still surface as `500`.

Future backend work should standardize request validation and storage exception handling across all routers.

## CORS and Docs

`ALLOWED_ORIGINS` controls CORS. The default allows:

```text
http://localhost:3000,http://127.0.0.1:3000
```

The backend serves custom HTML API documentation at `/docs`. This is not FastAPI/Swagger; it is maintained directly inside `main.py`.

## Known Risks

- The default `SECRET_KEY` is development-only and must be overridden outside local development.
- Request validation is manual and inconsistent.
- Quiz score casting can still raise if non-numeric values reach `int()`.
- SQLite is simple and reliable locally but not a multi-worker shared production database.
- Supabase RLS is disabled in the provided schema because the backend owns auth and uses server-side credentials.
