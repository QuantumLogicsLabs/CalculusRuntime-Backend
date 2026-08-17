# CalculusRuntime — Backend

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Starlette](https://img.shields.io/badge/Starlette-REST%20API-06B6D4?style=flat-square&logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-local%20db-003B57?style=flat-square&logo=sqlite&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-cloud%20db-3ECF8E?style=flat-square&logo=supabase&logoColor=white)
![JWT](https://img.shields.io/badge/Auth-JWT%20%2B%20bcrypt-FB923C?style=flat-square&logo=jsonwebtokens&logoColor=white)
![License](https://img.shields.io/badge/License-Proprietary-red?style=flat-square)
![Status](https://img.shields.io/badge/status-active-brightgreen?style=flat-square)

> **Starlette · Python 3.10+ · SQLite / Supabase · Zero bloat.**
> The API powering CalculusRuntime's user accounts, learning progress, bookmarks, quizzes, and solver history.

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Database](#database)
- [API Reference](#api-reference)
- [Authentication](#authentication)
- [License](#license)

---

## Overview

CalculusRuntime's backend is a lean, dependency-light REST API built on [Starlette](https://www.starlette.io/). It handles everything that needs to persist between sessions — who you are, how far you've gotten, what you've bookmarked, your best quiz scores, and your solver history.

No FastAPI. No Pydantic. No ORM. No `python-dotenv`. Just clean async Python and a storage layer that transparently switches between a local SQLite file and Supabase — your choice, one env var.

---

## Tech Stack

![Starlette](https://img.shields.io/badge/-Starlette-06B6D4?style=flat-square&logo=fastapi&logoColor=white)
![PyJWT](https://img.shields.io/badge/-PyJWT-FB923C?style=flat-square&logo=jsonwebtokens&logoColor=white)
![bcrypt](https://img.shields.io/badge/-bcrypt-6D28D9?style=flat-square&logoColor=white)
![SQLite](https://img.shields.io/badge/-SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)
![Supabase](https://img.shields.io/badge/-Supabase-3ECF8E?style=flat-square&logo=supabase&logoColor=white)
![Uvicorn](https://img.shields.io/badge/-Uvicorn-4B5563?style=flat-square&logo=gunicorn&logoColor=white)

| Layer            | Choice                                            |
| ---------------- | ------------------------------------------------- |
| Web framework    | Starlette                                         |
| Auth             | PyJWT + bcrypt (HS256, 7-day tokens)              |
| Database (local) | SQLite via stdlib `sqlite3` + `asyncio.to_thread` |
| Database (cloud) | Supabase (Postgres) via `supabase-py`             |
| Server           | Uvicorn                                           |
| Python           | 3.10 → 3.14 ✓                                     |

---

## Project Structure

```
backend/
├── main.py               # App entry point, routing, CORS, lifespan
├── core/
│   ├── auth_utils.py     # JWT creation/decoding, bcrypt hashing, request helpers
│   ├── storage.py        # Unified async storage layer (SQLite ↔ Supabase)
│   ├── db.py             # Raw SQLite helpers wrapped in asyncio.to_thread
│   ├── pdf_utils.py      # Certificate PDF rendering
│   ├── qr_utils.py       # Certificate QR code generation
│   └── quiz_bank.py      # Server-side certification quiz question bank
├── routers/
│   ├── auth.py           # POST /signup, POST /login, GET /me
│   ├── progress.py       # GET /, POST /section/complete, DELETE /section/{id}
│   ├── bookmarks.py      # GET /, POST /, DELETE /{id}
│   ├── quiz.py           # GET /, POST /
│   ├── solver_proxy.py   # POST /log, GET /history
│   ├── certificates.py   # POST /generate, GET /verify
│   └── verification.py   # POST /api/verify-course
├── services/
│   └── course_verification.py
├── docs/                 # Architecture, setup, and workflow docs
├── supabase_schema.sql   # Schema + RLS setup for Supabase
├── requirements.txt
└── .env.example
```

---

## Getting Started

### 1. Clone & create a virtual environment

```bash
git clone <repo-url>
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env — see Environment Variables below
```

### 4. Run

```bash
uvicorn main:app --reload --port 8000
```

The API will be live at `http://localhost:8000`.
Visit `http://localhost:8000/docs` for the interactive endpoint reference.

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```env
# Required — use a long, random string in production
SECRET_KEY=replace-with-a-long-random-string

# Token lifetime in minutes (default: 10080 = 7 days)
TOKEN_EXPIRE_MINUTES=10080

# --- Storage backend ---
# Set PROGRESS_DB=supabase to use Supabase; omit or set to "sqlite" for local SQLite
PROGRESS_DB=supabase

# SQLite path (used when PROGRESS_DB != supabase)
DB_PATH=calculusruntime.db

# Supabase (required when PROGRESS_DB=supabase)
SUPABASE_URL=https://xyzcompany.supabase.co
SUPABASE_SERVICE_ROLE_KEY=replace-with-your-backend-only-service-role-key

# CORS — comma-separated list of allowed origins
ALLOWED_ORIGINS=http://localhost:3000
```

> [!WARNING]
> **Never commit `.env` to version control.** It's already in `.gitignore`, but double-check before pushing. Rotate any keys that may have been exposed.

---

## Database

### SQLite (local / default)

![SQLite](https://img.shields.io/badge/mode-local%20SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)

No setup required. The database file is created automatically on first run. WAL mode and foreign keys are enabled out of the box.

### Supabase

![Supabase](https://img.shields.io/badge/mode-Supabase%20cloud-3ECF8E?style=flat-square&logo=supabase&logoColor=white)

1. Set `PROGRESS_DB=supabase` in your `.env`.
2. Open your Supabase project → **SQL Editor**.
3. Run `supabase_schema.sql` — creates all tables, indexes, and disables RLS on app-managed tables.
4. Use your **service role key** (not the anon/publishable key) as `SUPABASE_SERVICE_ROLE_KEY`. CalculusRuntime manages its own JWT auth; Supabase Auth is not used.

> [!IMPORTANT]
> RLS is intentionally disabled on these tables — auth is handled entirely by the backend. Re-enabling RLS without adding policies will block all requests with a `500` error.

**Schema overview:**

| Table            | Purpose                                     |
| ---------------- | ------------------------------------------- |
| `users`          | Accounts (username, email, hashed password) |
| `sections`       | Per-user completed section tracking         |
| `bookmarks`      | Saved content bookmarks                     |
| `quiz_scores`    | Best score per quiz per user                |
| `solver_history` | Last 50 solver expressions + results        |

---

## API Reference

![Auth](https://img.shields.io/badge/Auth-Bearer%20JWT-FB923C?style=flat-square&logo=jsonwebtokens&logoColor=white)

All protected routes require:

```
Authorization: Bearer <token>
```

Obtain a token from `POST /api/auth/signup` or `POST /api/auth/login`.

---

### Auth — `/api/auth`

| Method | Path               | Auth | Body                             | Description                 |
| ------ | ------------------ | ---- | -------------------------------- | --------------------------- |
| `POST` | `/api/auth/signup` | —    | `{ username, password, email? }` | Create account, returns JWT |
| `POST` | `/api/auth/login`  | —    | `{ username, password }`         | Sign in, returns JWT        |
| `GET`  | `/api/auth/me`     | 🔒   | —                                | Current user profile        |

### Progress — `/api/progress`

| Method   | Path                                 | Auth | Body             | Description                                                             |
| -------- | ------------------------------------ | ---- | ---------------- | ----------------------------------------------------------------------- |
| `GET`    | `/api/progress/`                     | 🔒   | —                | Full snapshot: completed sections, quiz scores, bookmarks, solver count |
| `POST`   | `/api/progress/section/complete`     | 🔒   | `{ section_id }` | Mark a section complete                                                 |
| `DELETE` | `/api/progress/section/{section_id}` | 🔒   | —                | Unmark a section                                                        |

### Bookmarks — `/api/bookmarks`

| Method   | Path                  | Auth | Body                  | Description                       |
| -------- | --------------------- | ---- | --------------------- | --------------------------------- |
| `GET`    | `/api/bookmarks/`     | 🔒   | —                     | List all bookmarks (newest first) |
| `POST`   | `/api/bookmarks/`     | 🔒   | `{ id, title, path }` | Add / upsert a bookmark           |
| `DELETE` | `/api/bookmarks/{id}` | 🔒   | —                     | Remove a bookmark                 |

### Quiz Scores — `/api/quiz`

| Method | Path         | Auth | Body                        | Description                            |
| ------ | ------------ | ---- | --------------------------- | -------------------------------------- |
| `GET`  | `/api/quiz/` | 🔒   | —                           | All quiz scores for current user       |
| `POST` | `/api/quiz/` | 🔒   | `{ quiz_id, score, total }` | Save score (best score wins on upsert) |

### Solver — `/api/solver`

| Method | Path                  | Auth     | Body                       | Description                 |
| ------ | --------------------- | -------- | -------------------------- | --------------------------- |
| `POST` | `/api/solver/log`     | optional | `{ expression?, result? }` | Log a solver interaction    |
| `GET`  | `/api/solver/history` | 🔒       | —                          | Last 50 solver interactions |

### System

| Method | Path          | Description                         |
| ------ | ------------- | ----------------------------------- |
| `GET`  | `/`           | API info + endpoint index (JSON)    |
| `GET`  | `/api/health` | Health check → `{ "status": "ok" }` |
| `GET`  | `/docs`       | Interactive HTML endpoint reference |

---

## Authentication

![JWT](https://img.shields.io/badge/HS256-JWT-FB923C?style=flat-square&logo=jsonwebtokens&logoColor=white)
![bcrypt](https://img.shields.io/badge/passwords-bcrypt-6D28D9?style=flat-square)

Tokens are HS256 JWTs signed with `SECRET_KEY`, valid for `TOKEN_EXPIRE_MINUTES` (default 7 days). Passwords are bcrypt-hashed before storage — plaintext passwords are never stored or returned.

```http
Authorization: Bearer <your-token>
```

---

## License

![License](https://img.shields.io/badge/License-Proprietary%20%E2%80%94%20QuantumLogics%20Inc.-red?style=flat-square)

© 2025 QuantumLogics Incorporated. All rights reserved.
This software is proprietary — see [LICENSE](./LICENSE) for the full terms.
