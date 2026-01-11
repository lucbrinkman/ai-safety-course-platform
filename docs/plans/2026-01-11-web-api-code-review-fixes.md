# Web API Code Review Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix remaining Important and Minor issues from the web_api code review.

**Architecture:** These are targeted fixes to existing endpoints - adding authentication where needed, fixing cookie security, and cleaning up code quality issues. No structural changes to the architecture.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic

---

## Summary of Issues to Fix

### Important (Fix First)
| # | Issue | File | Description |
|---|-------|------|-------------|
| 1 | Hardcoded `secure=False` | `web_api/auth.py:76` | Cookie not secure in production |
| 2 | No auth on `/transcribe` | `web_api/routes/speech.py` | API cost exposure |
| 3 | No auth on `/api/chat/lesson` | `web_api/routes/lesson.py` | API cost exposure |
| 4 | Dev fallback creates real user | `web_api/routes/lessons.py:93-105` | Pollutes production DB |
| 5 | Missing JWT_SECRET validation | `web_api/auth.py:16` | Delayed error detection |

### Minor (Fix After Important)
| # | Issue | File | Description |
|---|-------|------|-------------|
| 6 | Dead code | `web_api/main.py` | Unused legacy entry point |
| 7 | POST /auth/code returns 200 on error | `web_api/routes/auth.py:254-278` | Should return HTTP 400 |
| 8 | Session auth check duplication | `web_api/routes/lessons.py` | Same check repeated 3 times |
| 9 | Returns None instead of 204 | `web_api/routes/courses.py:25-26` | Unclear API contract |

---

## Task 1: Fix Cookie Secure Flag for Production

**Files:**
- Modify: `web_api/auth.py:72-79`

**Step 1: Add environment check**

Replace the `set_session_cookie` function to use environment-aware secure flag:

```python
def set_session_cookie(response: Response, token: str) -> None:
    """
    Set the session cookie with the JWT token.

    Args:
        response: The FastAPI response object
        token: The JWT token to store
    """
    is_production = bool(os.environ.get("RAILWAY_ENVIRONMENT"))
    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        max_age=60 * 60 * 24,  # 24 hours
    )
```

**Step 2: Verify the server starts**

Run: `python main.py --no-bot &` then `curl http://localhost:8000/health` then kill it.
Expected: Server starts, health check returns `{"status": "healthy", ...}`

**Step 3: Commit**

```bash
jj describe -m "fix(auth): make session cookie secure in production

Set secure=True when RAILWAY_ENVIRONMENT is set, fixing security
issue where cookies could be intercepted over HTTP in production."
```

---

## Task 2: Add Authentication to /transcribe Endpoint

**Files:**
- Modify: `web_api/routes/speech.py:1-36`

**Step 1: Add authentication dependency**

Update the imports and add `get_current_user` dependency:

```python
"""Speech-to-text API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from core.speech import transcribe_audio
from web_api.auth import get_current_user

router = APIRouter(prefix="/api", tags=["speech"])

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB (Whisper API limit)


@router.post("/transcribe")
async def transcribe(audio: UploadFile, user: dict = Depends(get_current_user)):
    """Transcribe audio to text using Whisper API.

    Requires authentication to prevent API cost abuse.
    Accepts audio files in webm, mp3, wav, m4a, flac, ogg formats.
    Returns the transcribed text.
    """
    contents = await audio.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(413, "File too large (max 25MB)")

    if not contents:
        raise HTTPException(400, "Empty audio file")

    try:
        text = await transcribe_audio(contents, audio.filename or "audio.webm")
        return {"text": text}
    except ValueError as e:
        # Missing API key
        raise HTTPException(500, str(e))
    except Exception as e:
        # API errors
        raise HTTPException(502, f"Transcription failed: {e}")
```

**Step 2: Verify the server starts**

Run: `python main.py --no-bot &` then `curl http://localhost:8000/health` then kill it.
Expected: Server starts without import errors.

**Step 3: Commit**

```bash
jj describe -m "fix(speech): require authentication for /transcribe

Add get_current_user dependency to prevent unauthenticated users
from using the Whisper API, which incurs costs per request."
```

---

## Task 3: Add Authentication to /api/chat/lesson Endpoint

**Files:**
- Modify: `web_api/routes/lesson.py:1-67`

**Step 1: Add authentication dependency**

Update imports and add `get_current_user` dependency:

```python
"""
Lesson chat API routes.

Endpoints:
- POST /api/chat/lesson - Send message and stream response
"""

import json
import sys
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core import lesson_chat
from web_api.auth import get_current_user

router = APIRouter(prefix="/api/chat", tags=["lesson"])


class ChatMessage(BaseModel):
    """A single chat message."""

    role: str  # "user" or "assistant"
    content: str


class LessonChatRequest(BaseModel):
    """Request body for lesson chat."""

    messages: list[ChatMessage]
    system_context: str | None = None


async def event_generator(messages: list[dict], system_context: str | None):
    """Generate SSE events from Claude stream."""
    try:
        async for chunk in lesson_chat.send_message(messages, system_context):
            yield f"data: {json.dumps(chunk)}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"


@router.post("/lesson")
async def chat_lesson(
    request: LessonChatRequest,
    user: dict = Depends(get_current_user),
) -> StreamingResponse:
    """
    Send a message to the lesson chat and stream the response.

    Requires authentication to prevent API cost abuse.

    Returns Server-Sent Events with:
    - {"type": "text", "content": "..."} for text chunks
    - {"type": "tool_use", "name": "transition_to_video"} when Claude wants to transition
    - {"type": "done"} when complete
    - {"type": "error", "message": "..."} on error
    """
    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    return StreamingResponse(
        event_generator(messages, request.system_context),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
```

**Step 2: Verify the server starts**

Run: `python main.py --no-bot &` then `curl http://localhost:8000/health` then kill it.
Expected: Server starts without import errors.

**Step 3: Commit**

```bash
jj describe -m "fix(lesson-chat): require authentication for /api/chat/lesson

Add get_current_user dependency to prevent unauthenticated users
from using the Claude API, which incurs costs per request."
```

---

## Task 4: Fix Dev Fallback User Creation

**Files:**
- Modify: `web_api/routes/lessons.py:93-106`

**Step 1: Guard dev fallback with DEV_MODE check**

Replace the `get_user_id_for_lesson` function:

```python
async def get_user_id_for_lesson(request: Request) -> int | None:
    """Get user_id from authenticated user, or None for anonymous requests.

    In DEV_MODE only, unauthenticated requests get a test user.
    In production, unauthenticated requests remain anonymous (user_id=None).
    """
    import os

    user_jwt = await get_optional_user(request)

    if user_jwt:
        # Authenticated user
        discord_id = user_jwt["sub"]
    elif os.environ.get("DEV_MODE", "").lower() in ("true", "1", "yes"):
        # Dev fallback: use a test discord_id (only in dev mode)
        discord_id = "dev_test_user_123"
    else:
        # Production: anonymous user (no database record)
        return None

    user = await get_or_create_user(discord_id)
    return user["user_id"]
```

**Step 2: Verify affected code paths handle None**

The code already handles `user_id=None` for anonymous sessions (check line 234, 376, 451). No changes needed.

**Step 3: Verify the server starts**

Run: `python main.py --no-bot &` then `curl http://localhost:8000/health` then kill it.
Expected: Server starts without errors.

**Step 4: Commit**

```bash
jj describe -m "fix(lessons): only create dev_test_user in DEV_MODE

Guard the dev fallback user creation with DEV_MODE check to prevent
polluting production database with test user records."
```

---

## Task 5: Add JWT_SECRET Startup Validation

**Files:**
- Modify: `web_api/auth.py:16-18`

**Step 1: Add startup validation**

Add validation right after the JWT_SECRET definition:

```python
JWT_SECRET = os.environ.get("JWT_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Validate JWT_SECRET at startup in production
if not JWT_SECRET and os.environ.get("RAILWAY_ENVIRONMENT"):
    raise RuntimeError("JWT_SECRET must be set in production (RAILWAY_ENVIRONMENT detected)")
```

**Step 2: Verify the server starts locally**

Run: `python main.py --no-bot &` then `curl http://localhost:8000/health` then kill it.
Expected: Server starts (no RAILWAY_ENVIRONMENT locally).

**Step 3: Commit**

```bash
jj describe -m "fix(auth): validate JWT_SECRET at startup in production

Fail fast if JWT_SECRET is not set when RAILWAY_ENVIRONMENT is
detected, rather than waiting for first authentication attempt."
```

---

## Task 6: Remove Dead Code - web_api/main.py

**Files:**
- Delete: `web_api/main.py`

**Step 1: Verify web_api/main.py is not imported anywhere**

Search for imports of web_api.main or "from web_api import main":

Run: `grep -r "web_api.main\|from web_api import main\|from web_api.main" --include="*.py" .`
Expected: No results (the file is only a legacy standalone entry).

**Step 2: Delete the file**

```bash
rm web_api/main.py
```

**Step 3: Verify the server starts**

Run: `python main.py --no-bot &` then `curl http://localhost:8000/health` then kill it.
Expected: Server starts without issues.

**Step 4: Commit**

```bash
jj describe -m "chore: remove dead code web_api/main.py

This legacy standalone entry point is not used. The unified backend
runs from root main.py which includes all routers."
```

---

## Task 7: Fix POST /auth/code to Return Proper HTTP Status

**Files:**
- Modify: `web_api/routes/auth.py:254-278`

**Step 1: Replace 200 with error JSON to proper HTTPException**

Replace the `validate_auth_code_api` function:

```python
@router.post("/code")
async def validate_auth_code_api(response: Response, code: str, next: str = "/"):
    """
    Validate a temporary auth code from the Discord bot (API version).

    Returns JSON response instead of redirect, for frontend fetch calls.
    Sets the session cookie on the response.
    """
    if not code:
        raise HTTPException(status_code=400, detail="missing_code")

    auth_code, error = await validate_and_use_auth_code(code)
    if error:
        raise HTTPException(status_code=400, detail=error)

    # Get or create user
    discord_id = auth_code["discord_id"]
    user = await get_or_create_user(discord_id)
    discord_username = user.get("discord_username") or f"User_{discord_id[:8]}"

    # Create JWT and set cookie
    token = create_jwt(discord_id, discord_username)
    set_session_cookie(response, token)

    return {"status": "ok", "next": next}
```

**Step 2: Verify the server starts**

Run: `python main.py --no-bot &` then `curl http://localhost:8000/health` then kill it.
Expected: Server starts without errors.

**Step 3: Commit**

```bash
jj describe -m "fix(auth): return HTTP 400 for errors in POST /auth/code

Use HTTPException for error responses instead of returning 200 with
error in body. This follows REST conventions for error handling."
```

---

## Task 8: Extract Session Authorization Helper

**Files:**
- Modify: `web_api/routes/lessons.py`

**Step 1: Add helper function after imports (around line 45)**

Add after the existing helper functions:

```python
def check_session_access(session: dict, user_id: int | None) -> None:
    """Raise 403 if user doesn't own the session.

    Anonymous sessions (user_id=None in session) are accessible by anyone.
    Owned sessions require the requesting user_id to match.
    """
    if session["user_id"] is not None and session["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not your session")
```

**Step 2: Replace duplicate checks in get_session_state (line 234)**

Replace:
```python
    if session["user_id"] is not None and session["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not your session")
```

With:
```python
    check_session_access(session, user_id)
```

**Step 3: Replace duplicate check in send_message_endpoint (line 376)**

Same replacement.

**Step 4: Replace duplicate check in advance_session (line 451)**

Same replacement.

**Step 5: Verify the server starts**

Run: `python main.py --no-bot &` then `curl http://localhost:8000/health` then kill it.
Expected: Server starts without errors.

**Step 6: Commit**

```bash
jj describe -m "refactor(lessons): extract check_session_access helper

DRY up the session authorization check that was repeated 3 times.
No behavior change."
```

---

## Task 9: Fix courses.py to Return 204 No Content

**Files:**
- Modify: `web_api/routes/courses.py:1-31`

**Step 1: Add Response import and return 204**

Replace the file content:

```python
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
```

**Step 2: Run existing tests**

Run: `pytest web_api/tests/test_courses_api.py -v`
Expected: Tests pass (or need updating for new 204 behavior).

**Step 3: Commit**

```bash
jj describe -m "fix(courses): return 204 No Content when no next lesson

Return proper HTTP 204 instead of null JSON when there's no next
lesson in the course. This is cleaner REST API design."
```

---

## Final Verification

**Step 1: Run all tests**

Run: `pytest discord_bot/tests/ web_api/tests/ -v`
Expected: All tests pass.

**Step 2: Manual smoke test**

Run: `python main.py --dev --no-bot`
Expected: Server starts, can access health endpoint.

**Step 3: Create summary commit**

If all tasks were committed separately, squash or describe the final state:

```bash
jj log --limit 10  # Review recent commits
```

---

## Summary Checklist

- [ ] Task 1: Cookie secure flag (Important)
- [ ] Task 2: Auth on /transcribe (Important)
- [ ] Task 3: Auth on /api/chat/lesson (Important)
- [ ] Task 4: Dev fallback guard (Important)
- [ ] Task 5: JWT_SECRET startup validation (Important)
- [ ] Task 6: Remove web_api/main.py (Minor)
- [ ] Task 7: POST /auth/code HTTP status (Minor)
- [ ] Task 8: Session auth helper (Minor)
- [ ] Task 9: courses.py 204 response (Minor)
- [ ] Final: All tests pass
