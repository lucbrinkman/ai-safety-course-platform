# core/lessons/tests/test_loader.py
"""Tests for lesson loader."""

import yaml
from pathlib import Path

import pytest
from core.lessons.loader import load_lesson, get_available_lessons, LessonNotFoundError, LESSONS_DIR


def test_load_existing_lesson():
    """Should load a lesson from JSON file."""
    lesson = load_lesson("intro-to-ai-safety")
    assert lesson.id == "intro-to-ai-safety"
    assert lesson.title == "Introduction to AI Safety"
    assert len(lesson.stages) > 0


def test_load_nonexistent_lesson():
    """Should raise LessonNotFoundError for unknown lesson."""
    with pytest.raises(LessonNotFoundError):
        load_lesson("nonexistent-lesson")


def test_get_available_lessons():
    """Should return list of available lesson IDs."""
    lessons = get_available_lessons()
    assert isinstance(lessons, list)
    assert "intro-to-ai-safety" in lessons


def test_lessons_only_use_allowed_fields():
    """Lessons should only contain allowed fields - prevents external URLs and unknown fields."""
    # Allowlist of valid fields at each level
    ALLOWED_TOP_LEVEL = {"id", "title", "stages", "optionalResources"}

    ALLOWED_STAGE_BY_TYPE = {
        "article": {"type", "source", "from", "to"},
        "video": {"type", "source", "from", "to"},
        "chat": {"type", "instructions", "showUserPreviousContent", "showTutorPreviousContent"},
    }

    ALLOWED_OPTIONAL_RESOURCE = {"type", "title", "source", "description"}

    for lesson_file in LESSONS_DIR.glob("*.yaml"):
        with open(lesson_file) as f:
            data = yaml.safe_load(f)

        # Check top-level fields
        unknown_top = set(data.keys()) - ALLOWED_TOP_LEVEL
        if unknown_top:
            pytest.fail(
                f"Lesson '{lesson_file.name}' contains unknown top-level field(s): {unknown_top}. "
                f"Allowed fields: {ALLOWED_TOP_LEVEL}"
            )

        # Check stages
        for i, stage in enumerate(data.get("stages", [])):
            stage_type = stage.get("type")
            if stage_type not in ALLOWED_STAGE_BY_TYPE:
                pytest.fail(
                    f"Lesson '{lesson_file.name}' stage {i} has unknown type '{stage_type}'. "
                    f"Allowed types: {list(ALLOWED_STAGE_BY_TYPE.keys())}"
                )

            allowed = ALLOWED_STAGE_BY_TYPE[stage_type]
            unknown = set(stage.keys()) - allowed
            if unknown:
                pytest.fail(
                    f"Lesson '{lesson_file.name}' stage {i} (type={stage_type}) contains unknown field(s): {unknown}. "
                    f"Allowed fields for {stage_type}: {allowed}"
                )

        # Check optional resources if present
        for i, resource in enumerate(data.get("optionalResources", [])):
            unknown = set(resource.keys()) - ALLOWED_OPTIONAL_RESOURCE
            if unknown:
                pytest.fail(
                    f"Lesson '{lesson_file.name}' optionalResources[{i}] contains unknown field(s): {unknown}. "
                    f"Allowed fields: {ALLOWED_OPTIONAL_RESOURCE}"
                )
