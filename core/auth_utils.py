"""JWT + bcrypt password hashing. Pure stdlib + PyJWT + bcrypt."""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
import bcrypt
from starlette.requests import Request
from starlette.responses import JSONResponse

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production-use-a-long-random-string")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "10080"))  # 7 days


# ── Password ──────────────────────────────────────────────────────────────────


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


# ── JWT ───────────────────────────────────────────────────────────────────────


def create_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc)
        + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[int]:
    """Returns user_id int or None on failure."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except Exception:
        return None


# ── Request helpers ───────────────────────────────────────────────────────────


def get_token(request: Request) -> Optional[str]:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None


def require_user(request: Request) -> Optional[int]:
    """Returns user_id or None (caller raises 401 if needed)."""
    token = get_token(request)
    if not token:
        return None
    return decode_token(token)


def err(status: int, detail: str) -> JSONResponse:
    return JSONResponse({"detail": detail}, status_code=status)
