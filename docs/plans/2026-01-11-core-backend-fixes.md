# Core Backend Code Review Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix all remaining issues from the core/ backend code review (8 issues total)

**Architecture:** The core/ directory is platform-agnostic business logic used by both Discord bot and web API. All changes must maintain this separation - no Discord/FastAPI imports allowed.

**Tech Stack:** Python 3.11+, SQLAlchemy (async), httpx, pytz, Anthropic SDK

---

## Issues Summary

| Task | File | Issue | Severity |
|------|------|-------|----------|
| 1 | `core/data.py` | Missing JSON/IO error handling | Important |
| 2 | `core/availability.py` | Private pytz attribute access undocumented | Important |
| 3 | `core/users.py` | Type hints missing Optional | Minor |
| 4 | `core/lessons/sessions.py` | Extra database round-trips | Minor |
| 5 | `core/transcripts/tools.py` | Imports inside functions | Minor |
| 6 | `core/lesson_chat.py` + `core/lessons/chat.py` | Duplicate modules | Important |
| 7 | `core/stampy.py` | No HTTP error handling | Important |
| 8 | `core/lessons/content.py` | Duplicate frontmatter parsing | Minor |

---

## Task 1: Add Error Handling to core/data.py

**Files:**
- Modify: `core/data.py:18-30`

**Step 1: Add error handling to load_data()**

Replace lines 18-23:

```python
def load_data() -> dict:
    """Load all user data from the JSON file."""
    if not DATA_FILE.exists():
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Failed to load data from {DATA_FILE}: {e}")
        return {}
```

**Step 2: Add error handling to save_data()**

Replace lines 26-30:

```python
def save_data(data: dict) -> None:
    """Save all user data to the JSON file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        print(f"Error: Failed to save data to {DATA_FILE}: {e}")
        raise
```

**Step 3: Add error handling to load_courses()**

Replace lines 48-53:

```python
def load_courses() -> dict:
    """Load all course data from the JSON file."""
    if not COURSES_FILE.exists():
        return {}
    try:
        with open(COURSES_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Failed to load courses from {COURSES_FILE}: {e}")
        return {}
```

**Step 4: Add error handling to save_courses()**

Replace lines 56-60:

```python
def save_courses(data: dict) -> None:
    """Save all course data to the JSON file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(COURSES_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        print(f"Error: Failed to save courses to {COURSES_FILE}: {e}")
        raise
```

**Step 5: Commit**

```bash
jj describe -m "fix(core): add error handling to data.py file I/O operations

Handle JSONDecodeError and IOError in load/save functions.
Log warnings for load failures (graceful degradation) and
re-raise errors for save failures (callers need to know)."
```

---

## Task 2: Document Private pytz Attribute in core/availability.py

**Files:**
- Modify: `core/availability.py:39-41`

**Step 1: Add documentation comment before private attribute access**

Add comment before line 40:

```python
    # Note: Using pytz private attribute _utc_transition_times.
    # This is necessary because pytz doesn't expose a public API for DST transitions.
    # If this breaks in a future pytz version, consider migrating to python-dateutil.
    if not hasattr(tz, '_utc_transition_times') or not tz._utc_transition_times:
        return []  # No DST for this timezone
```

**Step 2: Add same comment at second usage (line 47)**

The loop at line 47 uses the same attribute - the comment above covers both usages since they're in the same function.

**Step 3: Commit**

```bash
jj describe -m "docs(core): document private pytz attribute usage in availability.py

Add explanatory comment about _utc_transition_times being private
and the rationale for using it (no public API alternative)."
```

---

## Task 3: Improve Type Hints in core/users.py

**Files:**
- Modify: `core/users.py:30-36, 64-70`

**Step 1: Update save_user_profile type hints**

Replace lines 30-36:

```python
async def save_user_profile(
    discord_id: str,
    nickname: str | None = None,
    timezone_str: str | None = None,
    availability_local: str | None = None,
    if_needed_availability_local: str | None = None,
) -> dict[str, Any]:
```

**Step 2: Update update_user_profile type hints**

Replace lines 64-70:

```python
async def update_user_profile(
    discord_id: str,
    nickname: str | None = None,
    email: str | None = None,
    timezone_str: str | None = None,
    availability_local: str | None = None,
) -> dict[str, Any] | None:
```

**Step 3: Commit**

```bash
jj describe -m "style(core): use explicit Optional type hints in users.py

Replace implicit None defaults with explicit str | None type hints
for better clarity and IDE support."
```

---

## Task 4: Optimize Database Round-Trips in core/lessons/sessions.py

**Files:**
- Modify: `core/lessons/sessions.py:91-120, 123-146, 149-169`

**Step 1: Optimize add_message() to use RETURNING**

Replace lines 91-120:

```python
async def add_message(session_id: int, role: str, content: str, icon: str | None = None) -> dict:
    """
    Add a message to session history.

    Args:
        session_id: The session ID
        role: "user", "assistant", or "system"
        content: Message content
        icon: Optional icon type for system messages ("article", "video", "chat")

    Returns:
        Updated session dict
    """
    session = await get_session(session_id)
    message = {"role": role, "content": content}
    if icon:
        message["icon"] = icon
    messages = session["messages"] + [message]

    async with get_transaction() as conn:
        result = await conn.execute(
            update(lesson_sessions)
            .where(lesson_sessions.c.session_id == session_id)
            .values(
                messages=messages,
                last_active_at=datetime.now(timezone.utc),
            )
            .returning(lesson_sessions)
        )
        row = result.mappings().one()
        return dict(row)
```

**Step 2: Optimize advance_stage() to use RETURNING**

Replace lines 123-146:

```python
async def advance_stage(session_id: int) -> dict:
    """
    Move to the next stage.

    Args:
        session_id: The session ID

    Returns:
        Updated session dict
    """
    session = await get_session(session_id)
    new_index = session["current_stage_index"] + 1

    async with get_transaction() as conn:
        result = await conn.execute(
            update(lesson_sessions)
            .where(lesson_sessions.c.session_id == session_id)
            .values(
                current_stage_index=new_index,
                last_active_at=datetime.now(timezone.utc),
            )
            .returning(lesson_sessions)
        )
        row = result.mappings().one()
        return dict(row)
```

**Step 3: Optimize complete_session() to use RETURNING**

Replace lines 149-169:

```python
async def complete_session(session_id: int) -> dict:
    """
    Mark a session as completed.

    Args:
        session_id: The session ID

    Returns:
        Updated session dict
    """
    async with get_transaction() as conn:
        result = await conn.execute(
            update(lesson_sessions)
            .where(lesson_sessions.c.session_id == session_id)
            .values(
                completed_at=datetime.now(timezone.utc),
                last_active_at=datetime.now(timezone.utc),
            )
            .returning(lesson_sessions)
        )
        row = result.mappings().one()
        return dict(row)
```

**Step 4: Optimize claim_session() to use RETURNING**

Replace lines 194-204:

```python
    async with get_transaction() as conn:
        result = await conn.execute(
            update(lesson_sessions)
            .where(lesson_sessions.c.session_id == session_id)
            .values(
                user_id=user_id,
                last_active_at=datetime.now(timezone.utc),
            )
            .returning(lesson_sessions)
        )
        row = result.mappings().one()
        return dict(row)
```

**Step 5: Commit**

```bash
jj describe -m "perf(core): eliminate extra database round-trips in sessions.py

Use RETURNING clause in update statements to get updated row
in single query instead of separate get_session() call."
```

---

## Task 5: Move Imports to Module Level in core/transcripts/tools.py

**Files:**
- Modify: `core/transcripts/tools.py:1-30, 100, 116-117, 223`

**Step 1: Add imports at module level**

Add after line 27 (after `from pathlib import Path`):

```python
import json
import re
```

**Step 2: Remove inline import in get_text_at_time()**

Remove line 100 (`import json`)

**Step 3: Remove inline import in normalize_for_matching()**

Remove line 116-117 (`import re`)

**Step 4: Remove inline import in get_time_from_text()**

Remove line 223 (`import json`)

**Step 5: Commit**

```bash
jj describe -m "style(core): move json/re imports to module level in tools.py

Move imports from inside functions to top of file for consistency
and slight performance improvement (avoids repeated import lookups)."
```

---

## Task 6: Remove Duplicate Module core/lesson_chat.py

**Files:**
- Delete: `core/lesson_chat.py`
- Modify: `core/__init__.py:58, 92`

**Step 1: Verify core/lessons/chat.py is the complete version**

`core/lessons/chat.py` (195 lines) has:
- Stage-aware prompting
- Debug mode
- Tool filtering by stage type

`core/lesson_chat.py` (87 lines) has:
- Simple prompting only

The stage-aware version is more complete.

**Step 2: Check for imports of core/lesson_chat.py**

Run: `grep -r "from core import lesson_chat" . --include="*.py"`
Run: `grep -r "from core.lesson_chat" . --include="*.py"`

If any imports exist, update them to use `core.lessons.chat` instead.

**Step 3: Remove import from core/__init__.py**

Remove line 58: `from . import lesson_chat`

**Step 4: Remove from __all__ in core/__init__.py**

Remove line 92: `'lesson_chat',`

**Step 5: Delete the duplicate file**

```bash
rm core/lesson_chat.py
```

**Step 6: Commit**

```bash
jj describe -m "refactor(core): remove duplicate lesson_chat.py module

The stage-aware version in core/lessons/chat.py is the complete
implementation. core/lesson_chat.py was a simpler legacy version."
```

---

## Task 7: Add HTTP Error Handling to core/stampy.py

**Files:**
- Modify: `core/stampy.py:22-51`

**Step 1: Wrap HTTP operations with try/except**

Replace lines 22-51:

```python
async def ask(query: str) -> AsyncIterator[tuple[str, Any]]:
    """
    Send query to Stampy and stream response.

    Yields (state, content) tuples where:
    - state="thinking": content is thinking text
    - state="streaming": content is answer text
    - state="citations": content is list of citation dicts
    - state="error": content is error message
    No history - each question is independent.
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                STAMPY_API_URL,
                json={
                    "query": query,
                    "sessionId": "discord-ask-stampy",
                    "stream": True,
                },
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue

                    try:
                        data = json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue

                    state = data.get("state")
                    if state in ("thinking", "streaming"):
                        content = data.get("content", "")
                        if content:
                            yield (state, content)
                    elif state == "citations":
                        citations = data.get("citations", [])
                        if citations:
                            yield ("citations", citations)
    except httpx.HTTPStatusError as e:
        yield ("error", f"Stampy API error: {e.response.status_code}")
    except httpx.TimeoutException:
        yield ("error", "Stampy API request timed out")
    except httpx.RequestError as e:
        yield ("error", f"Network error: {e}")
```

**Step 2: Commit**

```bash
jj describe -m "fix(core): add HTTP error handling to stampy.py

Handle HTTP errors, timeouts, and network errors gracefully.
Yield error tuples instead of raising exceptions so callers
can display user-friendly error messages."
```

---

## Task 8: DRY Frontmatter Parsing in core/lessons/content.py

**Files:**
- Modify: `core/lessons/content.py:45-80, 178-213`

**Step 1: Create generic frontmatter parser**

Add after the dataclass definitions (after line 42):

```python
def _parse_frontmatter_generic(
    text: str,
    field_mapping: dict[str, str],
) -> tuple[dict[str, str], str]:
    """
    Generic YAML frontmatter parser.

    Args:
        text: Full markdown text, possibly with frontmatter
        field_mapping: Dict mapping YAML keys to output field names
                       e.g., {"source_url": "source_url", "video_id": "video_id"}

    Returns:
        Tuple of (metadata_dict, content_without_frontmatter)
    """
    pattern = r'^---\s*\n(.*?)\n---\s*\n'
    match = re.match(pattern, text, re.DOTALL)

    if not match:
        return {}, text

    frontmatter_text = match.group(1)
    content = text[match.end():]

    metadata = {}
    for line in frontmatter_text.split('\n'):
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key in field_mapping:
                metadata[field_mapping[key]] = value

    return metadata, content
```

**Step 2: Refactor parse_frontmatter() to use generic parser**

Replace lines 45-80:

```python
def parse_frontmatter(text: str) -> tuple[ArticleMetadata, str]:
    """
    Parse YAML frontmatter from markdown text.

    Args:
        text: Full markdown text, possibly with frontmatter

    Returns:
        Tuple of (metadata, content_without_frontmatter)
    """
    field_mapping = {
        "title": "title",
        "author": "author",
        "source_url": "source_url",
    }
    raw_metadata, content = _parse_frontmatter_generic(text, field_mapping)

    return ArticleMetadata(
        title=raw_metadata.get("title"),
        author=raw_metadata.get("author"),
        source_url=raw_metadata.get("source_url"),
    ), content
```

**Step 3: Refactor parse_video_frontmatter() to use generic parser**

Replace lines 178-213:

```python
def parse_video_frontmatter(text: str) -> tuple[VideoTranscriptMetadata, str]:
    """
    Parse YAML frontmatter from video transcript markdown.

    Args:
        text: Full markdown text, possibly with frontmatter

    Returns:
        Tuple of (metadata, transcript_without_frontmatter)
    """
    field_mapping = {
        "video_id": "video_id",
        "title": "title",
        "url": "url",
    }
    raw_metadata, content = _parse_frontmatter_generic(text, field_mapping)

    return VideoTranscriptMetadata(
        video_id=raw_metadata.get("video_id"),
        title=raw_metadata.get("title"),
        url=raw_metadata.get("url"),
    ), content
```

**Step 4: Commit**

```bash
jj describe -m "refactor(core): DRY frontmatter parsing in content.py

Extract common frontmatter parsing logic into _parse_frontmatter_generic()
and have parse_frontmatter() and parse_video_frontmatter() use it."
```

---

## Final Step: Create Summary Commit

After all tasks are complete:

```bash
jj new -m "chore(core): complete code review fixes for core/ directory

Fixes applied:
- Added error handling to data.py file I/O operations
- Documented private pytz attribute usage in availability.py
- Added explicit Optional type hints in users.py
- Optimized database round-trips in sessions.py using RETURNING
- Moved imports to module level in transcripts/tools.py
- Removed duplicate lesson_chat.py module
- Added HTTP error handling to stampy.py
- DRYed frontmatter parsing in content.py"
```

---

## Verification

After all changes, run:

```bash
# Check for syntax errors
python -m py_compile core/data.py core/availability.py core/users.py core/lessons/sessions.py core/transcripts/tools.py core/stampy.py core/lessons/content.py

# Run any existing tests
pytest discord_bot/tests/ -v
```
