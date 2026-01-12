# web_api/routes/courses.py
"""Course API routes."""

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response

from core.lessons.course_loader import (
    load_course,
    get_next_lesson,
    CourseNotFoundError,
)
from core.lessons import (
    load_lesson,
    get_user_lesson_progress,
    get_stage_title,
    get_stage_duration,
    LessonNotFoundError,
)
from web_api.auth import get_optional_user
from core import get_or_create_user

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.get("/{course_slug}/next-lesson")
async def get_next_lesson_endpoint(
    course_slug: str,
    current: str = Query(..., description="Current lesson slug"),
):
    """Get the next lesson after the current one.

    Returns 204 No Content if there is no next lesson (end of course).
    """
    try:
        result = get_next_lesson(course_slug, current)
    except CourseNotFoundError:
        raise HTTPException(status_code=404, detail=f"Course not found: {course_slug}")

    if result is None:
        return Response(status_code=204)

    return {
        "nextLessonSlug": result.lesson_slug,
        "nextLessonTitle": result.lesson_title,
    }


@router.get("/{course_slug}/progress")
async def get_course_progress(course_slug: str, request: Request):
    """Get course structure with user progress.

    Returns course modules, lessons, and stages with completion status.
    """
    # Get user if authenticated
    user_jwt = await get_optional_user(request)
    user_id = None
    if user_jwt:
        discord_id = user_jwt["sub"]
        user = await get_or_create_user(discord_id)
        user_id = user["user_id"]

    # Load course structure
    try:
        course = load_course(course_slug)
    except CourseNotFoundError:
        raise HTTPException(status_code=404, detail=f"Course not found: {course_slug}")

    # Get user's progress
    progress = await get_user_lesson_progress(user_id)

    # Build response with progress merged
    modules = []
    for module in course.modules:
        lessons = []
        for lesson_slug in module.lessons:
            try:
                lesson = load_lesson(lesson_slug)
            except LessonNotFoundError:
                continue

            lesson_progress = progress.get(lesson_slug, {
                "status": "not_started",
                "current_stage_index": None,
                "session_id": None,
            })

            # Build stages info
            stages = []
            for stage in lesson.stages:
                stages.append({
                    "type": stage.type,
                    "title": get_stage_title(stage),
                    "duration": get_stage_duration(stage) or None,
                    "optional": getattr(stage, "optional", False),
                })

            lessons.append({
                "slug": lesson.slug,
                "title": lesson.title,
                "stages": stages,
                "status": lesson_progress["status"],
                "currentStageIndex": lesson_progress["current_stage_index"],
                "sessionId": lesson_progress["session_id"],
            })

        modules.append({
            "id": module.id,
            "title": module.title,
            "lessons": lessons,
        })

    return {
        "course": {
            "slug": course.slug,
            "title": course.title,
        },
        "modules": modules,
    }
