"""Auth routes — signup, login, me."""

from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse

import storage
from auth_utils import hash_password, verify_password, create_token, require_user, err


def storage_err(exc: Exception):
    message = str(exc)
    if "public.users" in message and "schema cache" in message:
        return err(
            500,
            "Supabase table public.users is missing. Run backend/supabase_schema.sql in the Supabase SQL Editor, then restart the backend.",
        )
    if "row-level security" in message or "42501" in message:
        return err(
            500,
            "Supabase RLS is blocking this request. Re-run backend/supabase_schema.sql in the Supabase SQL Editor, or use a backend-only Supabase service role/secret key.",
        )
    return err(500, f"Database error: {message}")


async def signup(request: Request):
    try:
        body = await request.json()
    except Exception:
        return err(400, "Invalid JSON.")

    username = (body.get("username") or "").strip()
    password = body.get("password") or ""
    email = body.get("email") or None

    if len(username) < 3:
        return err(400, "Username must be at least 3 characters.")
    if len(password) < 6:
        return err(400, "Password must be at least 6 characters.")

    try:
        existing = await storage.get_user_by_username(username)
    except Exception as exc:
        return storage_err(exc)
    if existing:
        return err(409, "Username already taken.")

    hashed = hash_password(password)
    try:
        user_id = await storage.create_user(username, email, hashed)
    except Exception as exc:
        return storage_err(exc)
    token = create_token(user_id)
    return JSONResponse(
        {
            "access_token": token,
            "token_type": "bearer",
            "user": {"id": user_id, "username": username},
        },
        status_code=201,
    )


async def login(request: Request):
    try:
        body = await request.json()
    except Exception:
        return err(400, "Invalid JSON.")

    username = (body.get("username") or "").strip()
    password = body.get("password") or ""

    try:
        row = await storage.get_user_by_username(username)
    except Exception as exc:
        return storage_err(exc)
    if not row or not verify_password(password, row["hashed_pw"]):
        return err(401, "Incorrect username or password.")

    token = create_token(row["id"])
    return JSONResponse(
        {
            "access_token": token,
            "token_type": "bearer",
            "user": {"id": row["id"], "username": row["username"]},
        }
    )


async def me(request: Request):
    user_id = require_user(request)
    if not user_id:
        return err(401, "Not authenticated.")
    try:
        row = await storage.get_user_profile(user_id)
    except Exception as exc:
        return storage_err(exc)
    if not row:
        return err(401, "Session expired. Please sign in again.")
    return JSONResponse(row)


routes = [
    Route("/signup", signup, methods=["POST"]),
    Route("/login", login, methods=["POST"]),
    Route("/me", me, methods=["GET"]),
]
