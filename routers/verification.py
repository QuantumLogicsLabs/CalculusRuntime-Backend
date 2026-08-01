from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from services.course_verification import generate_verification_response

async def verify_course(request: Request):
    """
    Endpoint handler for POST /api/verify-course
    Reads raw JSON body without Pydantic and invokes the verification logic.
    """
    try:
        # Extract JSON body directly from the Starlette Request
        data = await request.json()
    except Exception:
        return JSONResponse(
            {"status": "error", "message": "Invalid or missing JSON body."},
            status_code=400
        )

    user_progress = data.get("userProgress")
    course_data = data.get("courseData")

    # Call the verification core logic from backend/services/course_verification.py
    response_data = generate_verification_response(user_progress, course_data)
    
    # Determine HTTP status code based on response status
    status_code = 400 if response_data.get("status") == "error" else 200
    return JSONResponse(response_data, status_code=status_code)

# Export the routes list so main.py can mount it with Mount("/api/verify-course", routes=verification_routes)
routes = [
    Route("/", verify_course, methods=["POST"]),
]