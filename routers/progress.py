"""Progress routes — full snapshot, mark/unmark sections."""

from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse

from storage import (
    get_progress,
    mark_section_complete,
    unmark_section_complete,
    set_leaderboard_opt_in,
)
from auth_utils import require_user, err


async def get_progress_route(request: Request):
    user_id = require_user(request)
    if not user_id:
        return err(401, "Not authenticated.")

    progress = await get_progress(user_id)
    return JSONResponse(progress)


async def mark_complete(request: Request):
    user_id = require_user(request)
    if not user_id:
        return err(401, "Not authenticated.")
    try:
        body = await request.json()
    except Exception:
        return err(400, "Invalid JSON.")

    section_id = (body.get("section_id") or "").strip()
    if not section_id:
        return err(400, "section_id required.")

    try:
        completed_at = await mark_section_complete(user_id, section_id)
    except PermissionError:
        return err(401, "Session expired. Please sign in again.")
    except Exception as exc:
        message = str(exc)
        if "FOREIGN KEY" in message or "foreign key" in message.lower():
            return err(401, "Session expired. Please sign in again.")
        return err(500, f"Could not mark section complete: {message}")

    return JSONResponse({"ok": True, "section_id": section_id, "completed_at": completed_at})


async def unmark_complete(request: Request):
    user_id = require_user(request)
    if not user_id:
        return err(401, "Not authenticated.")

    section_id = request.path_params.get("section_id", "")
    await unmark_section_complete(user_id, section_id)
    return JSONResponse({"ok": True})


async def set_leaderboard_opt_in_route(request: Request):
    user_id = require_user(request)
    if not user_id:
        return err(401, "Not authenticated.")
    try:
        body = await request.json()
    except Exception:
        return err(400, "Invalid JSON.")

    if "opt_in" not in body:
        return err(400, "opt_in required.")

    opted = await set_leaderboard_opt_in(user_id, bool(body.get("opt_in")))
    return JSONResponse({"ok": True, "leaderboardOptIn": opted})


routes = [
    Route("/", get_progress_route, methods=["GET"]),
    Route("/section/complete", mark_complete, methods=["POST"]),
    Route("/section/{section_id}", unmark_complete, methods=["DELETE"]),
    Route("/leaderboard", set_leaderboard_opt_in_route, methods=["POST"]),
]
