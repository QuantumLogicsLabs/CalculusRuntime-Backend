"""Solver usage logging routes."""

from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse

from core import storage
from core.auth_utils import require_user, err


async def log_use(request: Request):
    """Frontend calls this after each solver interaction."""
    user_id = require_user(request)
    try:
        body = await request.json()
    except Exception:
        body = {}

    expression = body.get("expression") or None
    result = body.get("result") or None

    await storage.log_solver_use(user_id, expression, result)
    return JSONResponse({"ok": True})


async def get_history(request: Request):
    user_id = require_user(request)
    if not user_id:
        return JSONResponse([])

    return JSONResponse(await storage.list_solver_history(user_id))


routes = [
    Route("/log", log_use, methods=["POST"]),
    Route("/history", get_history, methods=["GET"]),
]
