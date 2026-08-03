"""
Course completion verification logic (Dev 2 scope — Team Epsilon).

Given a snapshot of a user's progress and a course's requirements, decides
whether the course counts as "complete". Called by routers/verification.py
(POST /api/verify-course).

Expected request-body shapes (client sends these directly, no DB lookup):

userProgress = {
    "userId": "123",
    "completedSections": ["limits-continuity/1", "limits-continuity/2"],
    "quizScores": {"limits-continuity": 85},
}

courseData = {
    "id": "limits-continuity",
    "title": "Limits & Continuity",
    "requiredSections": ["limits-continuity/1", "limits-continuity/2"],
    "requiredQuiz": "limits-continuity",   # optional
    "minQuizScore": 60,                     # optional, defaults below
}
"""

DEFAULT_MIN_QUIZ_SCORE = 60


def generate_verification_response(user_progress, course_data):
    """Build the JSON-serializable response for the verify-course endpoint.

    Returns {"status": "error", ...} for malformed input (→ HTTP 400).
    Otherwise returns {"status": "success"|"fail", "verified": bool, ...}
    (→ HTTP 200) describing exactly what's missing, if anything.
    """
    if not isinstance(user_progress, dict) or not isinstance(course_data, dict):
        return {
            "status": "error",
            "verified": False,
            "message": "userProgress and courseData must both be objects.",
        }

    course_id = course_data.get("id")
    if not course_id:
        return {
            "status": "error",
            "verified": False,
            "message": "courseData.id is required.",
        }

    # -- Section completion --------------------------------------------------
    required_sections = course_data.get("requiredSections") or []
    completed_sections = set(user_progress.get("completedSections") or [])
    missing_sections = [s for s in required_sections if s not in completed_sections]
    sections_complete = len(missing_sections) == 0

    # -- Quiz completion (optional requirement) -------------------------------
    required_quiz = course_data.get("requiredQuiz")
    min_quiz_score = course_data.get("minQuizScore", DEFAULT_MIN_QUIZ_SCORE)
    quiz_scores = user_progress.get("quizScores") or {}

    quiz_passed = True
    quiz_score = None
    if required_quiz:
        quiz_score = quiz_scores.get(required_quiz)
        quiz_passed = quiz_score is not None and quiz_score >= min_quiz_score

    verified = sections_complete and quiz_passed

    return {
        "status": "success" if verified else "fail",
        "verified": verified,
        "courseId": course_id,
        "sectionsComplete": sections_complete,
        "missingSections": missing_sections,
        "quizPassed": quiz_passed,
        "quizScore": quiz_score,
    }