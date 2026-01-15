# core/lessons/tests/test_content_validation.py
"""Content validation tests - verify real course content is well-formed.

These tests discover and validate actual content in educational_content/.
They should never hardcode specific lesson or course names.
"""

import yaml
import pytest
from pathlib import Path

from core.lessons.loader import (
    load_lesson,
    get_available_lessons,
    LESSONS_DIR,
    LessonNotFoundError,
)
from core.lessons.course_loader import (
    load_course,
    COURSES_DIR,
)
from core.lessons.types import LessonRef


# --- Course Content Validation ---


def get_all_course_slugs() -> list[str]:
    """Discover all course slugs from COURSES_DIR."""
    if not COURSES_DIR.exists():
        return []
    return [f.stem for f in COURSES_DIR.glob("*.yaml")]


@pytest.mark.parametrize("course_slug", get_all_course_slugs())
def test_course_loads_successfully(course_slug):
    """Each course file should load without errors."""
    course = load_course(course_slug)
    assert course.slug == course_slug
    assert course.title  # Has a title
    assert len(course.progression) > 0  # Has content


@pytest.mark.parametrize("course_slug", get_all_course_slugs())
def test_course_references_existing_lessons(course_slug):
    """All lessons referenced in a course should exist as files."""
    course = load_course(course_slug)
    available = set(get_available_lessons())

    for item in course.progression:
        if isinstance(item, LessonRef):
            assert item.slug in available, (
                f"Course '{course_slug}' references non-existent lesson: '{item.slug}'"
            )


# --- Lesson Content Validation ---


@pytest.mark.parametrize("lesson_slug", get_available_lessons())
def test_lesson_loads_successfully(lesson_slug):
    """Each lesson file should load without errors."""
    lesson = load_lesson(lesson_slug)
    assert lesson.slug == lesson_slug
    assert lesson.title  # Has a title
    assert len(lesson.stages) > 0  # Has stages


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


# --- Schema Validation ---


ALLOWED_TOP_LEVEL = {"slug", "title", "stages", "optionalResources"}

ALLOWED_STAGE_BY_TYPE = {
    "article": {"type", "source", "from", "to", "optional", "introduction"},
    "video": {"type", "source", "from", "to", "optional", "introduction", "from_seconds", "to_seconds"},
    "chat": {
        "type",
        "instructions",
        "showUserPreviousContent",
        "showTutorPreviousContent",
    },
}

ALLOWED_OPTIONAL_RESOURCE = {"type", "title", "source", "description"}


@pytest.mark.parametrize("lesson_file", list(LESSONS_DIR.glob("*.yaml")))
def test_lesson_uses_allowed_fields(lesson_file):
    """Lessons should only contain allowed fields."""
    with open(lesson_file) as f:
        data = yaml.safe_load(f)

    # Check top-level fields
    unknown_top = set(data.keys()) - ALLOWED_TOP_LEVEL
    assert not unknown_top, (
        f"Lesson '{lesson_file.name}' has unknown top-level fields: {unknown_top}"
    )

    # Check stages
    for i, stage in enumerate(data.get("stages", [])):
        stage_type = stage.get("type")
        assert stage_type in ALLOWED_STAGE_BY_TYPE, (
            f"Lesson '{lesson_file.name}' stage {i} has unknown type '{stage_type}'"
        )

        allowed = ALLOWED_STAGE_BY_TYPE[stage_type]
        unknown = set(stage.keys()) - allowed
        assert not unknown, (
            f"Lesson '{lesson_file.name}' stage {i} has unknown fields: {unknown}"
        )

    # Check optional resources
    for i, resource in enumerate(data.get("optionalResources", [])):
        unknown = set(resource.keys()) - ALLOWED_OPTIONAL_RESOURCE
        assert not unknown, (
            f"Lesson '{lesson_file.name}' optionalResources[{i}] has unknown fields: {unknown}"
        )
