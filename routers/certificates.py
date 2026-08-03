"""
Certificate QR Generation & Validation (Dev 3 scope — Team Epsilon).

Design choice: the certificate is a **signed JWT**, not a database row.
The QR code encodes a verification URL containing that token. Anyone who
scans it hits `verify_certificate`, which recomputes the JWT signature —
no database lookup needed. This keeps the module fully standalone, per
the task doc ("operates as a standalone utility service independent of
frontend design or full course logic").

Dev 4 (integration) is expected to call `POST /generate` only *after*
Dev 2's `/api/courses/verify-completion` has confirmed the user actually
finished the course — this module does not re-check completion itself.
"""

import os
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse

from auth_utils import require_user, err, SECRET_KEY, ALGORITHM
import qr_utils

# How long a certificate token stays cryptographically valid.
# Certificates are meant to last, so default is long (~10 years).
CERT_TOKEN_EXPIRE_DAYS = int(os.getenv("CERT_TOKEN_EXPIRE_DAYS", "3650"))

# Where the frontend's verification page lives — QR encodes this + ?token=
FRONTEND_VERIFY_URL = os.getenv(
    "FRONTEND_VERIFY_URL",
    "https://calculus-runtime-frontend-ten.vercel.app/verify",
)


def _sign_certificate(
    cert_id: str, user_id: int, username: str, course_id: str, course_title: str
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "cert_id": cert_id,
        "uid": user_id,
        "username": username,
        "course_id": course_id,
        "course_title": course_title,
        "iat": now,
        "exp": now + timedelta(days=CERT_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


async def generate_certificate(request: Request):
    """POST /api/certificates/generate
    🔒 Requires auth. Body: {"course_id", "course_title", "username"?}

    Returns a signed certificate token + QR code (SVG and PNG data URI)
    + the verify URL that the QR points to.
    """
    user_id = require_user(request)
    if not user_id:
        return err(401, "Not authenticated.")

    try:
        body = await request.json()
    except Exception:
        return err(400, "Invalid JSON.")

    course_id = (body.get("course_id") or "").strip()
    course_title = (body.get("course_title") or "").strip()
    username = (body.get("username") or "").strip() or f"user-{user_id}"

    if not course_id or not course_title:
        return err(400, "course_id and course_title are required.")

    cert_id = uuid.uuid4().hex
    token = _sign_certificate(cert_id, user_id, username, course_id, course_title)
    verify_url = f"{FRONTEND_VERIFY_URL}?token={token}"

    return JSONResponse(
        {
            "cert_id": cert_id,
            "token": token,
            "verify_url": verify_url,
            "qr_svg": qr_utils.generate_qr_svg(verify_url),
            "qr_png_base64": qr_utils.generate_qr_png_data_uri(verify_url),
            "issued_at": datetime.now(timezone.utc).isoformat(),
        },
        status_code=201,
    )


async def verify_certificate(request: Request):
    """GET /api/certificates/verify?token=...
    Public route (no auth) — this is what scanning the QR opens.
    """
    token = request.query_params.get("token", "")
    if not token:
        return err(400, "Missing token.")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        return JSONResponse({"valid": False, "reason": "expired"}, status_code=400)
    except Exception:
        return JSONResponse({"valid": False, "reason": "invalid_signature"}, status_code=400)

    return JSONResponse(
        {
            "valid": True,
            "cert_id": payload.get("cert_id"),
            "username": payload.get("username"),
            "course_id": payload.get("course_id"),
            "course_title": payload.get("course_title"),
            "issued_at": payload.get("iat"),
        }
    )


routes = [
    Route("/generate", generate_certificate, methods=["POST"]),
    Route("/verify", verify_certificate, methods=["GET"]),
]