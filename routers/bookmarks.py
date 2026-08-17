"""Bookmarks routes."""

from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse

from core import storage
from core.auth_utils import require_user, err


async def list_bookmarks(request: Request):
    user_id = require_user(request)
    if not user_id:
        return err(401, "Not authenticated.")

    return JSONResponse(await storage.list_bookmarks(user_id))


async def add_bookmark(request: Request):
    user_id = require_user(request)
    if not user_id:
        return err(401, "Not authenticated.")
    try:
        body = await request.json()
    except Exception:
        return err(400, "Invalid JSON.")

    bm_id = (body.get("id") or "").strip()
    title = (body.get("title") or "").strip()
    path = (body.get("path") or "").strip()

    if not bm_id or not title or not path:
        return err(400, "id, title, and path are required.")

    await storage.add_bookmark(user_id, bm_id, title, path)
    return JSONResponse({"ok": True}, status_code=201)


async def remove_bookmark(request: Request):
    user_id = require_user(request)
    if not user_id:
        return err(401, "Not authenticated.")

    bm_id = request.path_params.get("bm_id", "")
    await storage.remove_bookmark(user_id, bm_id)
    return JSONResponse({"ok": True})


routes = [
    Route("/", list_bookmarks, methods=["GET"]),
    Route("/", add_bookmark, methods=["POST"]),
    Route("/{bm_id}", remove_bookmark, methods=["DELETE"]),
]
