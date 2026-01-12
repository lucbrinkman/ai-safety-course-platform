# core/lessons/tests/test_courses.py
"""Tests for course loader."""

import pytest
from core.lessons.course_loader import (
    load_course,
    get_next_lesson,
    get_all_lesson_slugs,
    CourseNotFoundError,
)


def test_load_existing_course():
    """Should load a course from YAML file."""
    course = load_course("default")
    assert course.slug == "default"
    assert course.title == "AI Safety Fundamentals"
    assert len(course.modules) > 0
    assert len(course.modules[0].lessons) > 0


def test_load_nonexistent_course():
    """Should raise CourseNotFoundError for unknown course."""
    with pytest.raises(CourseNotFoundError):
        load_course("nonexistent-course")


def test_get_next_lesson_within_module():
    """Should return next lesson in same module."""
    result = get_next_lesson("default", "intro-to-ai-safety")
    assert result is not None
    assert result.lesson_slug == "intelligence-feedback-loop"


def test_get_next_lesson_end_of_course():
    """Should return None at end of course."""
    # Get the last lesson slug
    all_lessons = get_all_lesson_slugs("default")
    last_lesson = all_lessons[-1]
    result = get_next_lesson("default", last_lesson)
    assert result is None


def test_get_next_lesson_unknown_lesson():
    """Should return None for lesson not in course."""
    result = get_next_lesson("default", "nonexistent-lesson")
    assert result is None


def test_get_all_lesson_slugs():
    """Should return flat list of all lesson slugs in order."""
    lesson_slugs = get_all_lesson_slugs("default")
    assert isinstance(lesson_slugs, list)
    assert "intro-to-ai-safety" in lesson_slugs
    assert "intelligence-feedback-loop" in lesson_slugs
    # Order should be intro first
    assert lesson_slugs.index("intro-to-ai-safety") < lesson_slugs.index("intelligence-feedback-loop")


from core.lessons.loader import get_available_lessons, load_lesson


def test_all_lessons_have_unique_slugs():
    """All lesson YAML files should have unique slugs."""
    lesson_files = get_available_lessons()
    slugs_seen = {}

    for lesson_file in lesson_files:
        lesson = load_lesson(lesson_file)
        if lesson.slug in slugs_seen:
            pytest.fail(
                f"Duplicate lesson slug '{lesson.slug}' found in "
                f"'{lesson_file}.yaml' and '{slugs_seen[lesson.slug]}.yaml'"
            )
        slugs_seen[lesson.slug] = lesson_file


def test_course_manifest_references_existing_lessons():
    """All lesson slugs in course manifest should exist as files."""
    course = load_course("default")
    available = set(get_available_lessons())

    for module in course.modules:
        for lesson_slug in module.lessons:
            if lesson_slug not in available:
                pytest.fail(
                    f"Course 'default' references non-existent lesson: '{lesson_slug}' "
                    f"in module '{module.id}'"
                )
