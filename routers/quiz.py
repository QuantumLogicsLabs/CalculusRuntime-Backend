"""Quiz scores routes."""

from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse

import storage
from auth_utils import require_user, err

DEFAULT_MIN_QUIZ_SCORE = 80


async def list_scores(request: Request):
    user_id = require_user(request)
    if not user_id:
        return err(401, "Not authenticated.")

    return JSONResponse(await storage.list_quiz_scores(user_id))


async def save_score(request: Request):
    user_id = require_user(request)
    if not user_id:
        return err(401, "Not authenticated.")
    try:
        body = await request.json()
    except Exception:
        return err(400, "Invalid JSON.")

    quiz_id = (body.get("quiz_id") or "").strip()
    score = body.get("score")
    total = body.get("total")

    if not quiz_id or score is None or total is None:
        return err(400, "quiz_id, score, and total are required.")

    score, total = int(score), int(total)
    min_score = int(body.get("min_score") or DEFAULT_MIN_QUIZ_SCORE)
    passed = total > 0 and round(score / total * 100) >= min_score

    # Best score per quiz (used for certificate eligibility)...
    await storage.save_quiz_score(user_id, quiz_id, score, total)
    # ...and the full, permanent attempt history (never overwritten).
    await storage.record_quiz_attempt(user_id, quiz_id, score, total, passed)

    return JSONResponse({"ok": True, "passed": passed}, status_code=201)


async def list_attempts(request: Request):
    """GET /api/quiz/attempts?quiz_id=...
    🔒 Full attempt history for the current user (optionally filtered).
    """
    user_id = require_user(request)
    if not user_id:
        return err(401, "Not authenticated.")

    quiz_id = request.query_params.get("quiz_id") or None
    return JSONResponse(await storage.list_quiz_attempts(user_id, quiz_id))


routes = [
    Route("/", list_scores, methods=["GET"]),
    Route("/", save_score, methods=["POST"]),
    Route("/attempts", list_attempts, methods=["GET"]),
]
