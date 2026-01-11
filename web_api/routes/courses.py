# web_api/routes/courses.py
"""Course API routes."""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from core.lessons.course_loader import (
    get_next_lesson,
    CourseNotFoundError,
)

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.get("/{course_id}/next-lesson")
async def get_next_lesson_endpoint(
    course_id: str,
    current: str = Query(..., description="Current lesson ID"),
):
    """Get the next lesson after the current one.

    Returns 204 No Content if there is no next lesson (end of course).
    """
    try:
        result = get_next_lesson(course_id, current)
    except CourseNotFoundError:
        raise HTTPException(status_code=404, detail=f"Course not found: {course_id}")

    if result is None:
        return Response(status_code=204)

    return {
        "nextLessonId": result.lesson_id,
        "nextLessonTitle": result.lesson_title,
    }
