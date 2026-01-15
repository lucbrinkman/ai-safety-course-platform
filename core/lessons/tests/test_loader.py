# core/lessons/tests/test_loader.py
"""Tests for lesson loader logic.

These tests use fixtures to test the loading logic without depending on real content.
"""

import pytest
from core.lessons.loader import (
    load_lesson,
    get_available_lessons,
    LessonNotFoundError,
)


def test_load_existing_lesson(patch_lessons_dir):
    """Should load a lesson from YAML file."""
    lesson = load_lesson("test-basic")
    assert lesson.slug == "test-basic"
    assert lesson.title == "Test Basic Lesson"
    assert len(lesson.stages) == 2
    assert lesson.stages[0].type == "article"
    assert lesson.stages[1].type == "chat"


def test_load_nonexistent_lesson():
    """Should raise LessonNotFoundError for unknown lesson."""
    with pytest.raises(LessonNotFoundError):
        load_lesson("nonexistent-lesson")


def test_get_available_lessons(patch_lessons_dir):
    """Should return list of available lesson slugs."""
    lessons = get_available_lessons()
    assert isinstance(lessons, list)
    assert len(lessons) >= 1
    assert "test-basic" in lessons


def test_parse_optional_stages(patch_lessons_dir):
    """Should parse optional field on article and video stages."""
    lesson = load_lesson("test-optional-stages")

    assert lesson.stages[0].optional is False  # default
    assert lesson.stages[1].optional is True   # explicit article
    assert lesson.stages[2].optional is True   # explicit video
    assert not hasattr(lesson.stages[3], "optional")  # chat has no optional
