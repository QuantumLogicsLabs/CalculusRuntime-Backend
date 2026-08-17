"""Progress routes — full snapshot, mark/unmark sections + Objective 19 comprehensive API."""

from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse
from datetime import datetime

from core.storage import (
    get_progress,
    get_leaderboard,
    mark_section_complete,
    unmark_section_complete,
    set_leaderboard_opt_in,
)
from core.auth_utils import require_user, err

ALL_TOPICS = [
    "partial-derivatives",
    "vector-calculus",
    "limits-continuity",
    "multiple-integrals",
    "taylor-series",
    "lagrange-multipliers",
    "stokes-theorem",
    "divergence-curl",
]

ALL_GUIDE_PARTS = {
    "partial-derivatives":   2,
    "vector-calculus":       2,
    "limits-continuity":     2,
    "multiple-integrals":    2,
    "taylor-series":         2,
    "lagrange-multipliers":  2,
    "stokes-theorem":        2,
    "divergence-curl":       2,
}


def build_summary(user_id: str, raw: dict) -> dict:
    """
    raw = whatever get_progress() returns.
    Adjust the keys below to match your actual progress_store output.
    Expected raw structure:
    {
      "user":     { "id", "name", "email", "created_at" },
      "sections": { "section_id": { "completed": bool, "completed_at": str } },
      "quizzes":  { "topic": { "score": int, "completed": bool, "completed_at": str } },
      "practice": { "topic": { "attempts": int, "correct": int } },
    }
    """

    user_info  = raw.get("user",     {})
    sections   = raw.get("sections", {})
    quizzes    = raw.get("quizzes",  {})
    practice   = raw.get("practice", {})

    completed_topics = []
    for topic in ALL_TOPICS:
        part1 = sections.get(f"{topic}/1", {}).get("completed", False)
        part2 = sections.get(f"{topic}/2", {}).get("completed", False)
        if part1 and part2:
            completed_topics.append(topic)

    total_topics     = len(ALL_TOPICS)
    num_completed    = len(completed_topics)
    num_remaining    = total_topics - num_completed
    overall_progress = round((num_completed / total_topics) * 100) if total_topics else 0


    total_guide_parts     = sum(ALL_GUIDE_PARTS.values())
    completed_guide_parts = sum(
        1 for sid, data in sections.items() if data.get("completed", False)
    )

    guide_by_topic = []
    for topic, parts in ALL_GUIDE_PARTS.items():
        done = sum(
            1 for i in range(1, parts + 1)
            if sections.get(f"{topic}/{i}", {}).get("completed", False)
        )
        guide_by_topic.append({
            "topic":          topic,
            "totalParts":     parts,
            "completedParts": done,
            "percent":        round((done / parts) * 100) if parts else 0,
        })

    quiz_list      = list(quizzes.values())
    total_quizzes  = len(quiz_list)
    done_quizzes   = sum(1 for q in quiz_list if q.get("completed", False))
    scores         = [q["score"] for q in quiz_list if q.get("score") is not None]
    total_score    = sum(scores)
    avg_score      = round(total_score / len(scores)) if scores else 0
    last_quiz_date = max(
        (q.get("completed_at", "") for q in quiz_list if q.get("completed_at")),
        default=None
    )
    quiz_scores_list = [
        {
            "topic":        topic,
            "score":        data.get("score"),
            "completed_at": data.get("completed_at"),
        }
        for topic, data in quizzes.items()
        if data.get("completed", False)
    ]

    total_attempts = sum(p.get("attempts", 0) for p in practice.values())
    total_correct  = sum(p.get("correct",  0) for p in practice.values())
    accuracy       = round((total_correct / total_attempts) * 100) if total_attempts else 0
    practice_by_topic = [
        {
            "topic":    topic,
            "attempts": data.get("attempts", 0),
            "correct":  data.get("correct",  0),
            "accuracy": round((data.get("correct", 0) / data["attempts"]) * 100)
                        if data.get("attempts", 0) > 0 else 0,
        }
        for topic, data in practice.items()
    ]

    course_progress = []
    for topic in ALL_TOPICS:
        parts      = ALL_GUIDE_PARTS[topic]
        guide_done = sum(
            1 for i in range(1, parts + 1)
            if sections.get(f"{topic}/{i}", {}).get("completed", False)
        )
        quiz_info     = quizzes.get(topic, {})
        practice_info = practice.get(topic, {})
        course_progress.append({
            "topic":           topic,
            "topicCompleted":  topic in completed_topics,
            "guideParts":      guide_done,
            "totalGuideParts": parts,
            "guidePercent":    round((guide_done / parts) * 100) if parts else 0,
            "quizScore":       quiz_info.get("score"),
            "quizCompleted":   quiz_info.get("completed", False),
            "practiceAttempts":practice_info.get("attempts", 0),
            "practiceCorrect": practice_info.get("correct",  0),
        })

    all_dates = [
        data.get("completed_at")
        for data in list(sections.values()) + list(quizzes.values())
        if data.get("completed_at")
    ]
    last_activity = max(all_dates) if all_dates else None

    return {
        "success": True,
        "data": {
            "user": {
                "id":          user_info.get("id",         user_id),
                "name":        user_info.get("name",        ""),
                "email":       user_info.get("email",       ""),
                "memberSince": user_info.get("created_at",  ""),
            },
            "overall": {
                "progressPercent": overall_progress,
                "totalScore":      total_score,
                "avgScore":        avg_score,
            },
            "quizStats": {
                "total":      total_quizzes,
                "completed":  done_quizzes,
                "totalScore": total_score,
                "avgScore":   avg_score,
                "lastQuiz":   last_quiz_date,
                "scores":     quiz_scores_list,
            },
            "topicStats": {
                "total":         total_topics,
                "completed":     num_completed,
                "remaining":     num_remaining,
                "completedList": completed_topics,
            },
            "studyGuides": {
                "totalParts":     total_guide_parts,
                "completedParts": completed_guide_parts,
                "byTopic":        guide_by_topic,
            },
            "practice": {
                "totalAttempts": total_attempts,
                "totalCorrect":  total_correct,
                "accuracy":      accuracy,
                "byTopic":       practice_by_topic,
            },
            "courseProgress": course_progress,
            "lastActivity":   last_activity,
            "generatedAt":    datetime.utcnow().isoformat() + "Z",
        }
    }



async def get_progress_route(request: Request):
    """GET /progress/ — original simple progress snapshot."""
    user_id = require_user(request)
    if not user_id:
        return err(401, "Not authenticated.")

    progress = await get_progress(user_id)
    return JSONResponse(progress)


async def get_full_progress(request: Request):
    """GET /progress/summary — Objective 19 comprehensive progress API."""
    user_id = require_user(request)
    if not user_id:
        return err(401, "Not authenticated.")

    try:
        raw     = await get_progress(user_id)
        summary = build_summary(user_id, raw)
        return JSONResponse(summary)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def mark_complete(request: Request):
    """POST /progress/section/complete — mark a section as complete."""
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
    """DELETE /progress/section/{section_id} — unmark a section."""
    user_id = require_user(request)
    if not user_id:
        return err(401, "Not authenticated.")

    section_id = request.path_params.get("section_id", "")
    await unmark_section_complete(user_id, section_id)
    return JSONResponse({"ok": True})


async def get_leaderboard_route(request: Request):
    """Anonymized entries for all opted-in users. Public — no auth required."""
    entries = await get_leaderboard()
    return JSONResponse({"entries": entries})


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
    Route("/",                       get_progress_route, methods=["GET"]),
    Route("/summary",                get_full_progress,  methods=["GET"]),   # ← Objective 19
    Route("/section/complete",       mark_complete,      methods=["POST"]),
    Route("/section/{section_id}",   unmark_complete,    methods=["DELETE"]),
    Route("/", get_progress_route, methods=["GET"]),
    Route("/section/complete", mark_complete, methods=["POST"]),
    Route("/section/{section_id}", unmark_complete, methods=["DELETE"]),
    Route("/leaderboard", get_leaderboard_route, methods=["GET"]),
    Route("/leaderboard", set_leaderboard_opt_in_route, methods=["POST"]),
]
