# core/lessons/tests/test_courses.py
"""Tests for course loader.

Logic tests use fixtures in core/lessons/tests/fixtures/ via patch_all_dirs.
Content validation tests are in test_content_validation.py.
"""

import pytest
from core.lessons.course_loader import (
    load_course,
    get_next_lesson,
    get_all_lesson_slugs,
    get_lessons,
    get_required_lessons,
    get_due_by_meeting,
    CourseNotFoundError,
)
from core.lessons.types import Course, LessonRef, Meeting


def test_load_existing_course(patch_all_dirs):
    """Should load a course from YAML file."""
    course = load_course("test-course")
    assert course.slug == "test-course"
    assert course.title == "Test Course"
    assert len(course.progression) == 6  # 4 lessons + 2 meetings


def test_load_nonexistent_course():
    """Should raise CourseNotFoundError for unknown course."""
    with pytest.raises(CourseNotFoundError):
        load_course("nonexistent-course")


def test_get_next_lesson_within_module(patch_all_dirs):
    """Should return unit_complete when next item is a meeting."""
    # lesson-b is followed by meeting: 1 in test-course
    result = get_next_lesson("test-course", "lesson-b")
    assert result is not None
    assert result["type"] == "unit_complete"
    assert result["unit_number"] == 1


def test_get_next_lesson_returns_lesson(patch_all_dirs):
    """Should return next lesson when there's no meeting in between."""
    # lesson-a is followed by lesson-b in test-course
    result = get_next_lesson("test-course", "lesson-a")
    assert result is not None
    assert result["type"] == "lesson"
    assert result["slug"] == "lesson-b"
    assert result["title"] == "Lesson B"


def test_get_next_lesson_end_of_course(patch_all_dirs):
    """Should return None at end of course."""
    # lesson-d is the last item in test-course
    result = get_next_lesson("test-course", "lesson-d")
    assert result is None


def test_get_next_lesson_unknown_lesson(patch_all_dirs):
    """Should return None for lesson not in course."""
    result = get_next_lesson("test-course", "nonexistent-lesson")
    assert result is None


def test_get_all_lesson_slugs(patch_all_dirs):
    """Should return flat list of all lesson slugs in order."""
    lesson_slugs = get_all_lesson_slugs("test-course")
    assert lesson_slugs == ["lesson-a", "lesson-b", "lesson-c", "lesson-d"]


# --- Tests for new helper functions (Task 2) ---


def test_get_lessons():
    """get_lessons should return all LessonRefs excluding Meetings."""
    course = Course(
        slug="test",
        title="Test Course",
        progression=[
            LessonRef(slug="lesson-1"),
            LessonRef(slug="lesson-2", optional=True),
            Meeting(number=1),
            LessonRef(slug="lesson-3"),
        ],
    )
    lessons = get_lessons(course)
    assert len(lessons) == 3
    assert lessons[0].slug == "lesson-1"
    assert lessons[1].slug == "lesson-2"
    assert lessons[2].slug == "lesson-3"


def test_get_required_lessons():
    """get_required_lessons should return only non-optional LessonRefs."""
    course = Course(
        slug="test",
        title="Test Course",
        progression=[
            LessonRef(slug="lesson-1"),
            LessonRef(slug="lesson-2", optional=True),
            Meeting(number=1),
            LessonRef(slug="lesson-3"),
            LessonRef(slug="lesson-4", optional=True),
        ],
    )
    required = get_required_lessons(course)
    assert len(required) == 2
    assert required[0].slug == "lesson-1"
    assert required[1].slug == "lesson-3"


def test_get_due_by_meeting():
    """get_due_by_meeting should return the meeting number following a lesson."""
    course = Course(
        slug="test",
        title="Test Course",
        progression=[
            LessonRef(slug="lesson-1"),
            LessonRef(slug="lesson-2"),
            Meeting(number=1),
            LessonRef(slug="lesson-3"),
            Meeting(number=2),
        ],
    )
    assert get_due_by_meeting(course, "lesson-1") == 1
    assert get_due_by_meeting(course, "lesson-2") == 1
    assert get_due_by_meeting(course, "lesson-3") == 2


def test_get_due_by_meeting_no_following_meeting():
    """Lessons after the last meeting should return None for due_by_meeting."""
    course = Course(
        slug="test",
        title="Test Course",
        progression=[
            LessonRef(slug="lesson-1"),
            Meeting(number=1),
            LessonRef(slug="lesson-2"),
        ],
    )
    assert get_due_by_meeting(course, "lesson-1") == 1
    assert get_due_by_meeting(course, "lesson-2") is None


def test_get_due_by_meeting_unknown_lesson():
    """Unknown lesson slugs should return None for due_by_meeting."""
    course = Course(
        slug="test",
        title="Test Course",
        progression=[
            LessonRef(slug="lesson-1"),
            Meeting(number=1),
        ],
    )
    assert get_due_by_meeting(course, "nonexistent-lesson") is None


# --- Tests for course loader with progression format (Task 3) ---


def test_load_course_parses_progression_types(patch_all_dirs):
    """load_course should correctly parse LessonRefs and Meetings from YAML."""
    course = load_course("test-course")

    lesson_refs = [item for item in course.progression if isinstance(item, LessonRef)]
    meetings = [item for item in course.progression if isinstance(item, Meeting)]

    assert len(lesson_refs) == 4
    assert len(meetings) == 2

    # Check lesson refs
    assert lesson_refs[0].slug == "lesson-a"
    assert lesson_refs[2].optional is True  # lesson-c is optional

    # Check meetings
    assert meetings[0].number == 1
    assert meetings[1].number == 2
