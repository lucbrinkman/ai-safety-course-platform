# Test Refactor: Separate Logic Tests from Content Validation

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor lesson/course tests so logic tests use synthetic fixtures and content validation tests generically discover and validate real content.

**Architecture:**
- Logic tests use fixture files in `core/lessons/tests/fixtures/` with monkeypatching to isolate from real content
- Content validation tests iterate over all courses/lessons dynamically, with no hardcoded names
- Tests never break when course content changes (only when code logic changes or content is malformed)

**Tech Stack:** pytest, pytest fixtures, monkeypatch, yaml

---

## Task 1: Create Test Fixture Files

**Files:**
- Create: `core/lessons/tests/fixtures/lessons/test-basic.yaml`
- Create: `core/lessons/tests/fixtures/lessons/test-optional-stages.yaml`
- Create: `core/lessons/tests/fixtures/courses/test-course.yaml`

**Step 1: Create fixtures directory structure**

```bash
mkdir -p core/lessons/tests/fixtures/lessons
mkdir -p core/lessons/tests/fixtures/courses
```

**Step 2: Create test-basic.yaml lesson fixture**

```yaml
# core/lessons/tests/fixtures/lessons/test-basic.yaml
slug: test-basic
title: Test Basic Lesson

stages:
  - type: article
    source: articles/test.md
  - type: chat
    instructions: Test instructions
    showUserPreviousContent: true
    showTutorPreviousContent: true
```

**Step 3: Create test-optional-stages.yaml lesson fixture**

```yaml
# core/lessons/tests/fixtures/lessons/test-optional-stages.yaml
slug: test-optional-stages
title: Test Optional Stages

stages:
  - type: article
    source: articles/test.md
  - type: article
    source: articles/optional.md
    optional: true
  - type: video
    source: videos/test.md
    optional: true
    introduction: Video intro text
  - type: chat
    instructions: Discuss the content
```

**Step 4: Create test-course.yaml course fixture**

```yaml
# core/lessons/tests/fixtures/courses/test-course.yaml
slug: test-course
title: Test Course

progression:
  - lesson: lesson-a
  - lesson: lesson-b
  - meeting: 1
  - lesson: lesson-c
    optional: true
  - meeting: 2
  - lesson: lesson-d
```

**Step 5: Create minimal lesson files for course fixture**

```yaml
# core/lessons/tests/fixtures/lessons/lesson-a.yaml
slug: lesson-a
title: Lesson A
stages:
  - type: chat
    instructions: Lesson A instructions
```

```yaml
# core/lessons/tests/fixtures/lessons/lesson-b.yaml
slug: lesson-b
title: Lesson B
stages:
  - type: chat
    instructions: Lesson B instructions
```

```yaml
# core/lessons/tests/fixtures/lessons/lesson-c.yaml
slug: lesson-c
title: Lesson C
stages:
  - type: chat
    instructions: Lesson C instructions
```

```yaml
# core/lessons/tests/fixtures/lessons/lesson-d.yaml
slug: lesson-d
title: Lesson D
stages:
  - type: chat
    instructions: Lesson D instructions
```

**Step 6: Commit**

```bash
jj desc -m "Add test fixtures for lesson/course logic tests"
```

---

## Task 2: Create Pytest Fixtures for Directory Patching

**Files:**
- Modify: `core/lessons/tests/conftest.py`

**Step 1: Add fixtures_dir and patching fixtures to conftest.py**

Add this to the end of `conftest.py`:

```python
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_lessons_dir():
    """Return path to test fixtures lessons directory."""
    return FIXTURES_DIR / "lessons"


@pytest.fixture
def fixtures_courses_dir():
    """Return path to test fixtures courses directory."""
    return FIXTURES_DIR / "courses"


@pytest.fixture
def patch_lessons_dir(monkeypatch, fixtures_lessons_dir):
    """Patch LESSONS_DIR to use test fixtures."""
    import core.lessons.loader as loader_module
    monkeypatch.setattr(loader_module, "LESSONS_DIR", fixtures_lessons_dir)


@pytest.fixture
def patch_courses_dir(monkeypatch, fixtures_courses_dir):
    """Patch COURSES_DIR to use test fixtures."""
    import core.lessons.course_loader as course_loader_module
    monkeypatch.setattr(course_loader_module, "COURSES_DIR", fixtures_courses_dir)


@pytest.fixture
def patch_all_dirs(patch_lessons_dir, patch_courses_dir):
    """Patch both LESSONS_DIR and COURSES_DIR to use test fixtures."""
    pass  # Just combines the two patches
```

**Step 2: Verify fixtures are importable**

```bash
pytest core/lessons/tests/conftest.py --collect-only
```

**Step 3: Commit**

```bash
jj desc -m "Add pytest fixtures for patching lesson/course directories"
```

---

## Task 3: Rewrite test_loader.py Logic Tests

**Files:**
- Modify: `core/lessons/tests/test_loader.py`

**Step 1: Rewrite test_load_existing_lesson to use fixtures**

Replace:
```python
def test_load_existing_lesson():
    """Should load a lesson from YAML file."""
    lesson = load_lesson("introduction")
    assert lesson.slug == "introduction"
    assert lesson.title == "Introduction"
    assert len(lesson.stages) > 0
```

With:
```python
def test_load_existing_lesson(patch_lessons_dir):
    """Should load a lesson from YAML file."""
    lesson = load_lesson("test-basic")
    assert lesson.slug == "test-basic"
    assert lesson.title == "Test Basic Lesson"
    assert len(lesson.stages) == 2
    assert lesson.stages[0].type == "article"
    assert lesson.stages[1].type == "chat"
```

**Step 2: Rewrite test_load_nonexistent_lesson (no change needed - already generic)**

Keep as-is:
```python
def test_load_nonexistent_lesson():
    """Should raise LessonNotFoundError for unknown lesson."""
    with pytest.raises(LessonNotFoundError):
        load_lesson("nonexistent-lesson")
```

**Step 3: Rewrite test_get_available_lessons to use fixtures**

Replace:
```python
def test_get_available_lessons():
    """Should return list of available lesson slugs."""
    lessons = get_available_lessons()
    assert isinstance(lessons, list)
    assert "introduction" in lessons
```

With:
```python
def test_get_available_lessons(patch_lessons_dir):
    """Should return list of available lesson slugs."""
    lessons = get_available_lessons()
    assert isinstance(lessons, list)
    assert len(lessons) >= 1
    assert "test-basic" in lessons
```

**Step 4: Rewrite test_parse_optional_stages to use fixtures**

Replace the entire test (which uses tmp_path/monkeypatch inline) with:
```python
def test_parse_optional_stages(patch_lessons_dir):
    """Should parse optional field on article and video stages."""
    lesson = load_lesson("test-optional-stages")

    assert lesson.stages[0].optional is False  # default
    assert lesson.stages[1].optional is True   # explicit article
    assert lesson.stages[2].optional is True   # explicit video
    assert not hasattr(lesson.stages[3], "optional")  # chat has no optional
```

**Step 5: Remove test_lessons_only_use_allowed_fields (move to content validation)**

Delete this test from test_loader.py - it validates real content, not logic.

**Step 6: Run tests to verify**

```bash
pytest core/lessons/tests/test_loader.py -v
```

**Step 7: Commit**

```bash
jj desc -m "Refactor test_loader.py to use fixtures for logic tests"
```

---

## Task 4: Rewrite test_courses.py Logic Tests

**Files:**
- Modify: `core/lessons/tests/test_courses.py`

**Step 1: Rewrite test_load_existing_course to use fixtures**

Replace:
```python
def test_load_existing_course():
    """Should load a course from YAML file."""
    course = load_course("default")
    assert course.slug == "default"
    assert course.title == "AI Safety Fundamentals"
    assert len(course.progression) > 0
```

With:
```python
def test_load_existing_course(patch_all_dirs):
    """Should load a course from YAML file."""
    course = load_course("test-course")
    assert course.slug == "test-course"
    assert course.title == "Test Course"
    assert len(course.progression) == 6  # 4 lessons + 2 meetings
```

**Step 2: Rewrite test_get_next_lesson_within_module**

Replace:
```python
def test_get_next_lesson_within_module():
    """Should return unit_complete when next item is a meeting."""
    result = get_next_lesson("default", "introduction")
    assert result is not None
    assert result["type"] == "unit_complete"
    assert result["unit_number"] == 1
```

With:
```python
def test_get_next_lesson_within_module(patch_all_dirs):
    """Should return unit_complete when next item is a meeting."""
    # lesson-b is followed by meeting: 1 in test-course
    result = get_next_lesson("test-course", "lesson-b")
    assert result is not None
    assert result["type"] == "unit_complete"
    assert result["unit_number"] == 1
```

**Step 3: Rewrite test_get_next_lesson_returns_lesson**

Replace:
```python
def test_get_next_lesson_returns_lesson():
    """Should return next lesson when there's no meeting in between."""
    result = get_next_lesson("default", "coming-soon")
    assert result is not None
```

With:
```python
def test_get_next_lesson_returns_lesson(patch_all_dirs):
    """Should return next lesson when there's no meeting in between."""
    # lesson-a is followed by lesson-b in test-course
    result = get_next_lesson("test-course", "lesson-a")
    assert result is not None
    assert result["type"] == "lesson"
    assert result["slug"] == "lesson-b"
    assert result["title"] == "Lesson B"
```

**Step 4: Rewrite test_get_next_lesson_end_of_course**

Replace:
```python
def test_get_next_lesson_end_of_course():
    # ... current complex implementation
```

With:
```python
def test_get_next_lesson_end_of_course(patch_all_dirs):
    """Should return None at end of course."""
    # lesson-d is the last item in test-course
    result = get_next_lesson("test-course", "lesson-d")
    assert result is None
```

**Step 5: Rewrite test_get_all_lesson_slugs**

Replace:
```python
def test_get_all_lesson_slugs():
    """Should return flat list of all lesson slugs in order."""
    lesson_slugs = get_all_lesson_slugs("default")
    assert isinstance(lesson_slugs, list)
    assert "introduction" in lesson_slugs
    assert "coming-soon" in lesson_slugs
    assert lesson_slugs.index("introduction") < lesson_slugs.index("coming-soon")
```

With:
```python
def test_get_all_lesson_slugs(patch_all_dirs):
    """Should return flat list of all lesson slugs in order."""
    lesson_slugs = get_all_lesson_slugs("test-course")
    assert lesson_slugs == ["lesson-a", "lesson-b", "lesson-c", "lesson-d"]
```

**Step 6: Remove content-dependent tests**

Delete these tests from test_courses.py (they'll move to content validation):
- `test_all_lessons_have_unique_slugs`
- `test_course_manifest_references_existing_lessons`
- `test_load_course_parses_progression_types` (keep but use fixtures)

**Step 7: Update test_load_course_parses_progression_types**

```python
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
```

**Step 8: Run tests**

```bash
pytest core/lessons/tests/test_courses.py -v
```

**Step 9: Commit**

```bash
jj desc -m "Refactor test_courses.py to use fixtures for logic tests"
```

---

## Task 5: Create Content Validation Tests

**Files:**
- Create: `core/lessons/tests/test_content_validation.py`

**Step 1: Create the content validation test file**

```python
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
```

**Step 2: Run content validation tests**

```bash
pytest core/lessons/tests/test_content_validation.py -v
```

**Step 3: Commit**

```bash
jj desc -m "Add content validation tests for courses and lessons"
```

---

## Task 6: Update web_api/tests/test_courses_api.py

**Files:**
- Modify: `web_api/tests/test_courses_api.py`

**Step 1: Rewrite API tests to use fixtures**

The API tests need to patch at a higher level since they go through FastAPI. We'll use dependency injection or accept that these tests validate the integration with real content.

For now, make these tests generic (not hardcoding lesson names):

```python
# web_api/tests/test_courses_api.py
"""Tests for course API endpoints."""

import pytest
from fastapi.testclient import TestClient
from main import app
from core.lessons.course_loader import load_course, get_all_lesson_slugs
from core.lessons.types import LessonRef, Meeting

client = TestClient(app)


def get_first_lesson_before_meeting(course_slug: str) -> str | None:
    """Find first lesson that's followed by a meeting."""
    course = load_course(course_slug)
    for i, item in enumerate(course.progression[:-1]):
        if isinstance(item, LessonRef) and isinstance(course.progression[i + 1], Meeting):
            return item.slug
    return None


def get_first_lesson_before_lesson(course_slug: str) -> str | None:
    """Find first lesson that's followed by another lesson."""
    course = load_course(course_slug)
    for i, item in enumerate(course.progression[:-1]):
        if isinstance(item, LessonRef) and isinstance(course.progression[i + 1], LessonRef):
            return item.slug
    return None


def test_get_next_lesson_returns_unit_complete():
    """Should return completedUnit when next item is a meeting."""
    lesson_slug = get_first_lesson_before_meeting("default")
    if lesson_slug is None:
        pytest.skip("No lesson→meeting pattern in default course")

    response = client.get(f"/api/courses/default/next-lesson?current={lesson_slug}")
    assert response.status_code == 200
    data = response.json()
    assert "completedUnit" in data


def test_get_next_lesson_returns_lesson():
    """Should return next lesson info when no meeting in between."""
    lesson_slug = get_first_lesson_before_lesson("default")
    if lesson_slug is None:
        pytest.skip("No lesson→lesson pattern in default course")

    response = client.get(f"/api/courses/default/next-lesson?current={lesson_slug}")
    assert response.status_code == 200
    data = response.json()
    assert "nextLessonSlug" in data
    assert "nextLessonTitle" in data


def test_get_next_lesson_invalid_course():
    """Should return 404 for invalid course."""
    response = client.get("/api/courses/nonexistent/next-lesson?current=any-lesson")
    assert response.status_code == 404


def test_get_course_progress_returns_units():
    """Should return course progress with units."""
    response = client.get("/api/courses/default/progress")
    assert response.status_code == 200
    data = response.json()

    assert "course" in data
    assert "units" in data
    assert len(data["units"]) >= 1

    # First unit should have expected structure
    unit = data["units"][0]
    assert "meetingNumber" in unit
    assert "lessons" in unit
```

**Step 2: Run API tests**

```bash
pytest web_api/tests/test_courses_api.py -v
```

**Step 3: Commit**

```bash
jj desc -m "Refactor API tests to discover course structure dynamically"
```

---

## Task 7: Run Full Test Suite and Cleanup

**Step 1: Run all affected tests**

```bash
pytest core/lessons/tests/ web_api/tests/test_courses_api.py -v
```

**Step 2: Fix any failures**

Review output and fix any remaining issues.

**Step 3: Final commit**

```bash
jj desc -m "Complete test refactor: logic tests use fixtures, content validation is generic"
```

**Step 4: Push to staging**

```bash
jj git push -b staging
```

---

## Summary

After this refactor:

| Test File | What It Tests | Uses Real Content? |
|-----------|---------------|-------------------|
| `test_loader.py` | Lesson loading logic | No - uses fixtures |
| `test_courses.py` | Course loading logic | No - uses fixtures |
| `test_content_validation.py` | Real content is valid | Yes - discovers all |
| `test_courses_api.py` | API works correctly | Yes - but generic |

**Benefits:**
- Logic tests never break when content changes
- Content validation automatically covers new lessons/courses
- Clear separation of concerns
