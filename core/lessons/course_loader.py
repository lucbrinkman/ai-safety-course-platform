# core/lessons/course_loader.py
"""Load course definitions from YAML files."""

import yaml
from pathlib import Path

from .types import Course, Module, LessonRef, Meeting
from .loader import load_lesson, LessonNotFoundError


class CourseNotFoundError(Exception):
    """Raised when a course cannot be found."""

    pass


COURSES_DIR = Path(__file__).parent.parent.parent / "educational_content" / "courses"


def load_course(course_slug: str) -> Course:
    """Load a course by slug from the courses directory."""
    course_path = COURSES_DIR / f"{course_slug}.yaml"

    if not course_path.exists():
        raise CourseNotFoundError(f"Course not found: {course_slug}")

    with open(course_path) as f:
        data = yaml.safe_load(f)

    # Parse progression items from YAML
    progression: list[LessonRef | Meeting] = []
    for item in data["progression"]:
        if "lesson" in item:
            progression.append(
                LessonRef(
                    slug=item["lesson"],
                    optional=item.get("optional", False),
                )
            )
        elif "meeting" in item:
            progression.append(Meeting(number=item["meeting"]))

    return Course(
        slug=data["slug"],
        title=data["title"],
        progression=progression,
    )


def get_all_lesson_slugs(course_slug: str) -> list[str]:
    """Get flat list of all lesson slugs in course order."""
    course = load_course(course_slug)
    return [item.slug for item in course.progression if isinstance(item, LessonRef)]


def get_next_lesson(course_slug: str, current_lesson_slug: str) -> dict | None:
    """Get what comes after the current lesson in the progression.

    Returns:
        - {"type": "lesson", "slug": str, "title": str} if next item is a lesson
        - {"type": "unit_complete", "unit_number": int} if next item is a meeting
        - None if end of course or lesson not found
    """
    course = load_course(course_slug)

    # Find the current lesson's index in progression
    current_index = None
    for i, item in enumerate(course.progression):
        if isinstance(item, LessonRef) and item.slug == current_lesson_slug:
            current_index = i
            break

    if current_index is None:
        return None  # Lesson not in this course

    # Look at the next item in progression
    next_index = current_index + 1
    if next_index >= len(course.progression):
        return None  # End of course

    next_item = course.progression[next_index]

    if isinstance(next_item, Meeting):
        return {"type": "unit_complete", "unit_number": next_item.number}

    if isinstance(next_item, LessonRef):
        try:
            next_lesson = load_lesson(next_item.slug)
            return {
                "type": "lesson",
                "slug": next_item.slug,
                "title": next_lesson.title,
            }
        except LessonNotFoundError:
            return None

    return None


def get_lessons(course: Course) -> list[LessonRef]:
    """Get all lesson references from a course, excluding meetings.

    Args:
        course: The course to get lessons from.

    Returns:
        List of LessonRef objects in progression order.
    """
    return [item for item in course.progression if isinstance(item, LessonRef)]


def get_required_lessons(course: Course) -> list[LessonRef]:
    """Get only required (non-optional) lesson references from a course.

    Args:
        course: The course to get required lessons from.

    Returns:
        List of non-optional LessonRef objects in progression order.
    """
    return [
        item
        for item in course.progression
        if isinstance(item, LessonRef) and not item.optional
    ]


def get_due_by_meeting(course: Course, lesson_slug: str) -> int | None:
    """Get the meeting number by which a lesson should be completed.

    Lessons are due by the next meeting that follows them in the progression.
    If there is no meeting after a lesson, returns None.

    Args:
        course: The course containing the lesson.
        lesson_slug: The slug of the lesson to check.

    Returns:
        Meeting number if there's a following meeting, None otherwise.
    """
    found_lesson = False

    for item in course.progression:
        if isinstance(item, LessonRef) and item.slug == lesson_slug:
            found_lesson = True
        elif found_lesson and isinstance(item, Meeting):
            return item.number

    return None
