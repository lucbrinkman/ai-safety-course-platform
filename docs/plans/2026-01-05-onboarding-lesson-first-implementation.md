# Lesson-First Onboarding Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Allow anonymous users to start lessons, then claim sessions after Discord OAuth.

**Architecture:** Sessions created with nullable user_id, stored in localStorage. After OAuth, claim endpoint assigns session to authenticated user. Frontend shows auth status and prompts login at appropriate moment.

**Tech Stack:** Python/FastAPI backend, PostgreSQL, React/TypeScript frontend, pytest for backend TDD, Vitest for frontend integration tests.

---

## Task 1: Database Migration - Nullable user_id

**Files:**
- Create: `migrations/003_nullable_session_user_id.sql`
- Modify: `core/tables.py:430-434`

**Step 1: Create migration file**

```sql
-- migrations/003_nullable_session_user_id.sql
-- Allow anonymous lesson sessions (user_id can be NULL until claimed)

ALTER TABLE lesson_sessions
ALTER COLUMN user_id DROP NOT NULL;

-- Add index for finding unclaimed sessions
CREATE INDEX idx_lesson_sessions_unclaimed
ON lesson_sessions (session_id)
WHERE user_id IS NULL;
```

**Step 2: Update SQLAlchemy table definition**

In `core/tables.py`, change line 433 from:
```python
        nullable=False,
```
to:
```python
        nullable=True,
```

**Step 3: Run migration**

Run: `psql $DATABASE_URL -f migrations/003_nullable_session_user_id.sql`
Expected: `ALTER TABLE` and `CREATE INDEX` success messages

**Step 4: Commit**

```bash
jj commit -m "feat: allow nullable user_id in lesson_sessions for anonymous users"
```

---

## Task 2: Backend - Claim Session Function (TDD)

**Files:**
- Modify: `core/lessons/tests/test_sessions.py`
- Modify: `core/lessons/sessions.py`
- Modify: `core/lessons/__init__.py`

### Step 1: Write failing test for claim_session

Add to `core/lessons/tests/test_sessions.py`:

```python
import pytest
from core.lessons.sessions import (
    create_session,
    get_session,
    claim_session,
    SessionNotFoundError,
    SessionAlreadyClaimedError,
)


@pytest.mark.asyncio
async def test_claim_unclaimed_session(test_user_id, another_test_user_id):
    """Claiming an unclaimed session assigns it to the user."""
    # Create anonymous session
    session = await create_session(user_id=None, lesson_id="test-lesson")
    assert session["user_id"] is None

    # Claim it
    claimed = await claim_session(session["session_id"], another_test_user_id)

    assert claimed["user_id"] == another_test_user_id
    assert claimed["session_id"] == session["session_id"]


@pytest.mark.asyncio
async def test_claim_already_claimed_session_fails(test_user_id, another_test_user_id):
    """Cannot claim a session that already has a user."""
    # Create session with user
    session = await create_session(user_id=test_user_id, lesson_id="test-lesson")

    # Try to claim it
    with pytest.raises(SessionAlreadyClaimedError):
        await claim_session(session["session_id"], another_test_user_id)


@pytest.mark.asyncio
async def test_claim_nonexistent_session_fails(test_user_id):
    """Cannot claim a session that doesn't exist."""
    with pytest.raises(SessionNotFoundError):
        await claim_session(99999, test_user_id)
```

### Step 2: Add test fixture for another_test_user_id

Add to `core/lessons/tests/conftest.py`:

```python
@pytest.fixture
async def another_test_user_id():
    """Create another test user and return their user_id."""
    user = await get_or_create_user("another_test_discord_id_456")
    return user["user_id"]
```

### Step 3: Run tests to verify they fail

Run: `pytest core/lessons/tests/test_sessions.py -v -k "claim"`
Expected: FAIL with `ImportError: cannot import name 'claim_session'`

### Step 4: Implement claim_session

Add to `core/lessons/sessions.py`:

```python
class SessionAlreadyClaimedError(Exception):
    """Raised when trying to claim a session that already has a user."""
    pass


async def claim_session(session_id: int, user_id: int) -> dict:
    """
    Claim an anonymous session for a user.

    Args:
        session_id: The session to claim
        user_id: The user claiming the session

    Returns:
        Updated session dict

    Raises:
        SessionNotFoundError: If session doesn't exist
        SessionAlreadyClaimedError: If session already has a user
    """
    session = await get_session(session_id)

    if session["user_id"] is not None:
        raise SessionAlreadyClaimedError(
            f"Session {session_id} already claimed by user {session['user_id']}"
        )

    async with get_transaction() as conn:
        await conn.execute(
            update(lesson_sessions)
            .where(lesson_sessions.c.session_id == session_id)
            .values(user_id=user_id)
        )

    return await get_session(session_id)
```

### Step 5: Export from __init__.py

Add to `core/lessons/__init__.py`:

```python
from .sessions import (
    # ... existing exports ...
    claim_session,
    SessionAlreadyClaimedError,
)
```

### Step 6: Run tests to verify they pass

Run: `pytest core/lessons/tests/test_sessions.py -v -k "claim"`
Expected: All PASS

### Step 7: Commit

```bash
jj commit -m "feat: add claim_session function for anonymous session claiming"
```

---

## Task 3: Backend - Anonymous Session Creation (TDD)

**Files:**
- Modify: `core/lessons/tests/test_sessions.py`
- Modify: `core/lessons/sessions.py`

### Step 1: Write failing test

Add to `core/lessons/tests/test_sessions.py`:

```python
@pytest.mark.asyncio
async def test_create_anonymous_session():
    """Can create a session without a user_id."""
    session = await create_session(user_id=None, lesson_id="test-lesson")

    assert session["user_id"] is None
    assert session["lesson_id"] == "test-lesson"
    assert session["session_id"] is not None
```

### Step 2: Run test to verify it fails

Run: `pytest core/lessons/tests/test_sessions.py::test_create_anonymous_session -v`
Expected: FAIL (likely integrity error or type error)

### Step 3: Update create_session signature

Modify `core/lessons/sessions.py` `create_session` function:

Change:
```python
async def create_session(user_id: int, lesson_id: str) -> dict:
```

To:
```python
async def create_session(user_id: int | None, lesson_id: str) -> dict:
```

### Step 4: Run test to verify it passes

Run: `pytest core/lessons/tests/test_sessions.py::test_create_anonymous_session -v`
Expected: PASS

### Step 5: Commit

```bash
jj commit -m "feat: allow anonymous session creation with user_id=None"
```

---

## Task 4: Backend - Claim Endpoint (TDD)

**Files:**
- Create: `web_api/tests/test_lessons_api.py`
- Modify: `web_api/routes/lessons.py`

### Step 1: Write failing test

Create `web_api/tests/test_lessons_api.py`:

```python
"""Tests for lesson API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from main import app


client = TestClient(app)


def test_claim_session_success():
    """Authenticated user can claim an anonymous session."""
    # Mock the auth to return a user
    with patch("web_api.routes.lessons.get_current_user") as mock_auth:
        mock_auth.return_value = {"sub": "test_discord_123", "username": "testuser"}

        # First create an anonymous session (mock the session)
        with patch("web_api.routes.lessons.claim_session") as mock_claim:
            mock_claim.return_value = {
                "session_id": 1,
                "user_id": 42,
                "lesson_id": "test",
                "messages": [],
            }

            response = client.post("/api/lesson-sessions/1/claim")

            assert response.status_code == 200
            assert response.json()["claimed"] is True


def test_claim_session_requires_auth():
    """Cannot claim a session without authentication."""
    with patch("web_api.routes.lessons.get_current_user") as mock_auth:
        mock_auth.side_effect = Exception("Not authenticated")

        response = client.post("/api/lesson-sessions/1/claim")

        # Should fail auth
        assert response.status_code in [401, 403, 500]


def test_claim_already_claimed_session():
    """Cannot claim a session that's already claimed."""
    with patch("web_api.routes.lessons.get_current_user") as mock_auth:
        mock_auth.return_value = {"sub": "test_discord_123", "username": "testuser"}

        with patch("web_api.routes.lessons.claim_session") as mock_claim:
            from core.lessons import SessionAlreadyClaimedError
            mock_claim.side_effect = SessionAlreadyClaimedError("Already claimed")

            response = client.post("/api/lesson-sessions/1/claim")

            assert response.status_code == 403
```

### Step 2: Run tests to verify they fail

Run: `pytest web_api/tests/test_lessons_api.py -v`
Expected: FAIL with 404 (endpoint doesn't exist)

### Step 3: Implement claim endpoint

Add to `web_api/routes/lessons.py`:

```python
from web_api.auth import get_current_user  # Add to imports
from core.lessons import claim_session, SessionAlreadyClaimedError  # Add to imports


@router.post("/lesson-sessions/{session_id}/claim")
async def claim_session_endpoint(session_id: int, request: Request):
    """Claim an anonymous session for the authenticated user."""
    # Require authentication
    user_jwt = await get_current_user(request)
    discord_id = user_jwt["sub"]

    # Get or create user record
    user = await get_or_create_user(discord_id)
    user_id = user["user_id"]

    try:
        await claim_session(session_id, user_id)
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
    except SessionAlreadyClaimedError:
        raise HTTPException(status_code=403, detail="Session already claimed")

    return {"claimed": True}
```

### Step 4: Run tests to verify they pass

Run: `pytest web_api/tests/test_lessons_api.py -v`
Expected: All PASS

### Step 5: Commit

```bash
jj commit -m "feat: add /api/lesson-sessions/{id}/claim endpoint"
```

---

## Task 5: Backend - Anonymous Session Access (TDD)

**Files:**
- Modify: `web_api/tests/test_lessons_api.py`
- Modify: `web_api/routes/lessons.py`

### Step 1: Write failing test

Add to `web_api/tests/test_lessons_api.py`:

```python
def test_get_anonymous_session_by_id():
    """Can access an anonymous session without auth if you have the session_id."""
    with patch("web_api.routes.lessons.get_optional_user") as mock_auth:
        mock_auth.return_value = None  # Not authenticated

        with patch("web_api.routes.lessons.get_session") as mock_get:
            mock_get.return_value = {
                "session_id": 1,
                "user_id": None,  # Anonymous
                "lesson_id": "test",
                "current_stage_index": 0,
                "messages": [],
                "completed_at": None,
            }

            with patch("web_api.routes.lessons.load_lesson") as mock_lesson:
                mock_lesson.return_value = MagicMock(
                    title="Test",
                    stages=[MagicMock(type="chat", instructions="hi", show_user_previous_content=True, show_tutor_previous_content=True)]
                )

                response = client.get("/api/lesson-sessions/1")

                # Should succeed for anonymous session
                assert response.status_code == 200
```

### Step 2: Run test to verify it fails

Run: `pytest web_api/tests/test_lessons_api.py::test_get_anonymous_session_by_id -v`
Expected: FAIL with 403 (current code requires user_id match)

### Step 3: Update session access logic

Modify `get_session_state` in `web_api/routes/lessons.py`:

Change the access check from:
```python
    if session["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not your session")
```

To:
```python
    # Allow access if:
    # 1. Session is anonymous (user_id is None) - anyone with session_id can access
    # 2. Session belongs to the requesting user
    if session["user_id"] is not None and session["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not your session")
```

Apply same change to `send_message_endpoint` and `advance_session`.

### Step 4: Run tests

Run: `pytest web_api/tests/test_lessons_api.py -v`
Expected: All PASS

### Step 5: Commit

```bash
jj commit -m "feat: allow anonymous access to unclaimed sessions"
```

---

## Task 6: Backend - Anonymous Session Creation Endpoint

**Files:**
- Modify: `web_api/routes/lessons.py`

### Step 1: Update start_session to allow anonymous

Modify `start_session` in `web_api/routes/lessons.py`:

Change:
```python
@router.post("/lesson-sessions")
async def start_session(
    request_body: CreateSessionRequest, request: Request
):
    """Start a new lesson session."""
    user_id = await get_user_id_for_lesson(request)
```

To:
```python
@router.post("/lesson-sessions")
async def start_session(
    request_body: CreateSessionRequest, request: Request
):
    """Start a new lesson session. Can be anonymous (no auth required)."""
    user_jwt = await get_optional_user(request)

    if user_jwt:
        discord_id = user_jwt["sub"]
        user = await get_or_create_user(discord_id)
        user_id = user["user_id"]
    else:
        user_id = None  # Anonymous session
```

### Step 2: Test manually

Run: `curl -X POST http://localhost:8000/api/lesson-sessions -H "Content-Type: application/json" -d '{"lesson_id": "intelligence-feedback-loop"}'`
Expected: `{"session_id": <number>}` without needing auth

### Step 3: Commit

```bash
jj commit -m "feat: allow anonymous session creation without authentication"
```

---

## Task 7: Frontend - API Client Updates

**Files:**
- Modify: `web_frontend/src/api/lessons.ts`

### Step 1: Add claimSession function

Add to `web_frontend/src/api/lessons.ts`:

```typescript
export async function claimSession(sessionId: number): Promise<{ claimed: boolean }> {
  const res = await fetch(`${API_BASE}/api/lesson-sessions/${sessionId}/claim`, {
    method: "POST",
    credentials: "include",
  });
  if (!res.ok) {
    if (res.status === 403) throw new Error("Session already claimed");
    if (res.status === 404) throw new Error("Session not found");
    throw new Error("Failed to claim session");
  }
  return res.json();
}
```

### Step 2: Commit

```bash
jj commit -m "feat: add claimSession API function"
```

---

## Task 8: Frontend - Session Storage Hook

**Files:**
- Create: `web_frontend/src/hooks/useAnonymousSession.ts`

### Step 1: Create the hook

```typescript
// web_frontend/src/hooks/useAnonymousSession.ts
import { useCallback } from "react";

const SESSION_KEY_PREFIX = "lesson_session_";

export function useAnonymousSession(lessonId: string) {
  const storageKey = `${SESSION_KEY_PREFIX}${lessonId}`;

  const getStoredSessionId = useCallback((): number | null => {
    const stored = localStorage.getItem(storageKey);
    return stored ? parseInt(stored, 10) : null;
  }, [storageKey]);

  const storeSessionId = useCallback((sessionId: number) => {
    localStorage.setItem(storageKey, sessionId.toString());
  }, [storageKey]);

  const clearSessionId = useCallback(() => {
    localStorage.removeItem(storageKey);
  }, [storageKey]);

  return {
    getStoredSessionId,
    storeSessionId,
    clearSessionId,
  };
}
```

### Step 2: Commit

```bash
jj commit -m "feat: add useAnonymousSession hook for localStorage session tracking"
```

---

## Task 9: Frontend - Auth Status Indicator

**Files:**
- Create: `web_frontend/src/components/unified-lesson/AuthStatusBanner.tsx`

### Step 1: Create component

```tsx
// web_frontend/src/components/unified-lesson/AuthStatusBanner.tsx
import { useAuth } from "../../hooks/useAuth";

interface Props {
  onLoginClick: () => void;
}

export default function AuthStatusBanner({ onLoginClick }: Props) {
  const { isAuthenticated, isLoading, discordUsername } = useAuth();

  if (isLoading) return null;

  if (isAuthenticated) {
    return (
      <div className="bg-green-50 border-b border-green-200 px-4 py-2 text-sm text-green-700 flex items-center gap-2">
        <span className="w-2 h-2 bg-green-500 rounded-full" />
        Signed in as {discordUsername}
      </div>
    );
  }

  return (
    <div className="bg-amber-50 border-b border-amber-200 px-4 py-2 text-sm text-amber-700 flex items-center justify-between">
      <span>Your progress is not being saved</span>
      <button
        onClick={onLoginClick}
        className="text-amber-800 font-medium hover:underline"
      >
        Sign in with Discord to save progress
      </button>
    </div>
  );
}
```

### Step 2: Commit

```bash
jj commit -m "feat: add AuthStatusBanner component"
```

---

## Task 10: Frontend - Auth Prompt Modal

**Files:**
- Create: `web_frontend/src/components/unified-lesson/AuthPromptModal.tsx`

### Step 1: Create component

```tsx
// web_frontend/src/components/unified-lesson/AuthPromptModal.tsx
interface Props {
  isOpen: boolean;
  onLogin: () => void;
  onDismiss: () => void;
}

export default function AuthPromptModal({ isOpen, onLogin, onDismiss }: Props) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4 shadow-xl">
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">
          Save Your Progress
        </h2>
        <p className="text-gray-600 mb-6">
          Sign in with Discord to save your progress and continue later.
        </p>
        <div className="flex flex-col gap-3">
          <button
            onClick={onLogin}
            className="w-full bg-indigo-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-indigo-700 transition-colors flex items-center justify-center gap-2"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
              <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515a.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0a12.64 12.64 0 0 0-.617-1.25a.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057a19.9 19.9 0 0 0 5.993 3.03a.078.078 0 0 0 .084-.028a14.09 14.09 0 0 0 1.226-1.994a.076.076 0 0 0-.041-.106a13.107 13.107 0 0 1-1.872-.892a.077.077 0 0 1-.008-.128a10.2 10.2 0 0 0 .372-.292a.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127a12.299 12.299 0 0 1-1.873.892a.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028a19.839 19.839 0 0 0 6.002-3.03a.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.956-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.955-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.946 2.418-2.157 2.418z"/>
            </svg>
            Sign in with Discord
          </button>
          <button
            onClick={onDismiss}
            className="w-full text-gray-600 py-2 px-4 hover:text-gray-800 transition-colors"
          >
            Continue without saving
          </button>
        </div>
      </div>
    </div>
  );
}
```

### Step 2: Commit

```bash
jj commit -m "feat: add AuthPromptModal component"
```

---

## Task 11: Frontend - Wire Up UnifiedLesson

**Files:**
- Modify: `web_frontend/src/pages/UnifiedLesson.tsx`

### Step 1: Import new components and hooks

Add imports:
```tsx
import { useAuth } from "../hooks/useAuth";
import { useAnonymousSession } from "../hooks/useAnonymousSession";
import { claimSession } from "../api/lessons";
import AuthStatusBanner from "../components/unified-lesson/AuthStatusBanner";
import AuthPromptModal from "../components/unified-lesson/AuthPromptModal";
```

### Step 2: Add state and hooks

Add near top of component:
```tsx
const { isAuthenticated, login } = useAuth();
const { getStoredSessionId, storeSessionId, clearSessionId } = useAnonymousSession(lessonId!);
const [showAuthPrompt, setShowAuthPrompt] = useState(false);
const [hasPromptedAuth, setHasPromptedAuth] = useState(false);
```

### Step 3: Modify session initialization

Replace the `init` function in the useEffect to check localStorage first:
```tsx
async function init() {
  // Check for existing anonymous session
  const storedId = getStoredSessionId();
  if (storedId) {
    try {
      const state = await getSession(storedId);
      setSessionId(storedId);
      setSession(state);

      // If user is now authenticated, try to claim the session
      if (isAuthenticated && state.user_id === null) {
        await claimSession(storedId);
      }
      return;
    } catch {
      // Session expired or invalid, create new one
      clearSessionId();
    }
  }

  // Create new session
  const sid = await createSession(lessonId!);
  storeSessionId(sid);
  setSessionId(sid);
  const state = await getSession(sid);
  setSession(state);
}
```

### Step 4: Trigger auth prompt on first non-chat stage completion

Modify `handleAdvanceStage` to show auth prompt:
```tsx
const handleAdvanceStage = useCallback(async () => {
  if (!sessionId) return;

  // If anonymous and completing first non-chat stage, prompt for auth
  const currentStage = session?.stages?.[session.current_stage_index];
  if (!isAuthenticated && !hasPromptedAuth && currentStage?.type !== "chat") {
    setShowAuthPrompt(true);
    setHasPromptedAuth(true);
    return; // Don't advance yet, wait for auth decision
  }

  // ... rest of existing advance logic
}, [sessionId, isAuthenticated, hasPromptedAuth, session]);
```

### Step 5: Add auth handlers

```tsx
const handleLoginClick = useCallback(() => {
  // Store that we're mid-lesson so we can return
  sessionStorage.setItem("returnToLesson", lessonId!);
  login();
}, [lessonId, login]);

const handleAuthDismiss = useCallback(async () => {
  setShowAuthPrompt(false);
  // Continue with the advance they initiated
  if (!sessionId) return;
  const result = await advanceStage(sessionId);
  // ... handle result
}, [sessionId]);
```

### Step 6: Add components to JSX

Add before main content:
```tsx
<AuthStatusBanner onLoginClick={handleLoginClick} />
```

Add modal:
```tsx
<AuthPromptModal
  isOpen={showAuthPrompt}
  onLogin={handleLoginClick}
  onDismiss={handleAuthDismiss}
/>
```

### Step 7: Commit

```bash
jj commit -m "feat: integrate anonymous session flow in UnifiedLesson"
```

---

## Task 12: Frontend - Homepage Buttons

**Files:**
- Modify: `web_frontend/src/pages/Home.tsx`

### Step 1: Update homepage

```tsx
import { Link } from "react-router-dom";

export default function Home() {
  return (
    <div className="py-16 max-w-2xl mx-auto text-center">
      <h1 className="text-4xl font-bold text-gray-900 mb-4">
        AI Safety Course Platform
      </h1>
      <p className="text-xl text-gray-600 mb-8">
        Learn about AI safety and alignment through interactive lessons.
      </p>

      <div className="flex flex-col sm:flex-row gap-4 justify-center">
        <Link
          to="/lesson/intelligence-feedback-loop"
          className="bg-indigo-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-indigo-700 transition-colors"
        >
          Start Learning
        </Link>
        <Link
          to="/signup"
          className="bg-white text-indigo-600 border-2 border-indigo-600 px-8 py-3 rounded-lg font-medium hover:bg-indigo-50 transition-colors"
        >
          Sign Up
        </Link>
      </div>

      <p className="text-sm text-gray-500 mt-6">
        Try our intro lesson first, or sign up directly for the full course.
      </p>
    </div>
  );
}
```

### Step 2: Commit

```bash
jj commit -m "feat: add Start Learning and Sign Up buttons to homepage"
```

---

## Task 13: Frontend - Update Completion Modal

**Files:**
- Modify: `web_frontend/src/components/unified-lesson/LessonCompleteModal.tsx`

### Step 1: Simplify to show signup CTA

Update the component to always show signup option when lesson is complete:

```tsx
import { Link } from "react-router-dom";

interface Props {
  isOpen: boolean;
  lessonTitle?: string;
}

export default function LessonCompleteModal({ isOpen, lessonTitle }: Props) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4 shadow-xl text-center">
        <div className="text-5xl mb-4">🎉</div>
        <h2 className="text-2xl font-semibold text-gray-900 mb-2">
          Lesson Complete!
        </h2>
        <p className="text-gray-600 mb-6">
          {lessonTitle ? `You've finished "${lessonTitle}".` : "Great work!"}{" "}
          Ready to continue your AI safety journey?
        </p>
        <div className="flex flex-col gap-3">
          <Link
            to="/signup"
            className="w-full bg-indigo-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-indigo-700 transition-colors"
          >
            Join the Full Course
          </Link>
          <Link
            to="/"
            className="w-full text-gray-600 py-2 px-4 hover:text-gray-800 transition-colors"
          >
            Return to Home
          </Link>
        </div>
      </div>
    </div>
  );
}
```

### Step 2: Commit

```bash
jj commit -m "feat: update LessonCompleteModal with signup CTA"
```

---

## Task 14: Frontend Integration Test

**Files:**
- Create: `web_frontend/src/__tests__/anonymous-session-flow.test.tsx`

### Step 1: Create integration test

```tsx
// web_frontend/src/__tests__/anonymous-session-flow.test.tsx
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

// Mock the API and auth
vi.mock("../api/lessons", () => ({
  createSession: vi.fn(),
  getSession: vi.fn(),
  claimSession: vi.fn(),
  advanceStage: vi.fn(),
  sendMessage: vi.fn(),
}));

vi.mock("../hooks/useAuth", () => ({
  useAuth: vi.fn(),
}));

import UnifiedLesson from "../pages/UnifiedLesson";
import * as lessonsApi from "../api/lessons";
import { useAuth } from "../hooks/useAuth";

describe("Anonymous Session Flow", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it("creates anonymous session and stores in localStorage", async () => {
    // Setup: not authenticated
    (useAuth as any).mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      login: vi.fn(),
    });

    (lessonsApi.createSession as any).mockResolvedValue(123);
    (lessonsApi.getSession as any).mockResolvedValue({
      session_id: 123,
      user_id: null,
      lesson_id: "test",
      current_stage_index: 0,
      messages: [],
      stages: [{ type: "chat" }],
      completed: false,
    });

    render(
      <MemoryRouter initialEntries={["/lesson/test"]}>
        <UnifiedLesson />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(lessonsApi.createSession).toHaveBeenCalledWith("test");
    });

    // Session ID should be stored
    expect(localStorage.getItem("lesson_session_test")).toBe("123");
  });

  it("claims session after authentication", async () => {
    // Setup: localStorage has session, user now authenticated
    localStorage.setItem("lesson_session_test", "123");

    (useAuth as any).mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
    });

    (lessonsApi.getSession as any).mockResolvedValue({
      session_id: 123,
      user_id: null, // Still unclaimed
      lesson_id: "test",
      current_stage_index: 0,
      messages: [{ role: "user", content: "hello" }],
      stages: [{ type: "chat" }],
      completed: false,
    });

    (lessonsApi.claimSession as any).mockResolvedValue({ claimed: true });

    render(
      <MemoryRouter initialEntries={["/lesson/test"]}>
        <UnifiedLesson />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(lessonsApi.claimSession).toHaveBeenCalledWith(123);
    });
  });

  it("shows auth prompt when anonymous user advances past first content stage", async () => {
    (useAuth as any).mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      login: vi.fn(),
    });

    (lessonsApi.createSession as any).mockResolvedValue(123);
    (lessonsApi.getSession as any).mockResolvedValue({
      session_id: 123,
      user_id: null,
      lesson_id: "test",
      current_stage_index: 1, // On article stage
      messages: [],
      stages: [{ type: "chat" }, { type: "article" }],
      current_stage: { type: "article" },
      completed: false,
    });

    render(
      <MemoryRouter initialEntries={["/lesson/test"]}>
        <UnifiedLesson />
      </MemoryRouter>
    );

    // Find and click the advance/done button
    await waitFor(() => {
      const doneButton = screen.queryByText(/done|continue/i);
      if (doneButton) fireEvent.click(doneButton);
    });

    // Auth prompt should appear
    await waitFor(() => {
      expect(screen.getByText(/save your progress/i)).toBeInTheDocument();
    });
  });
});
```

### Step 2: Run tests

Run: `cd web_frontend && npm test`
Expected: All PASS

### Step 3: Commit

```bash
jj commit -m "test: add integration tests for anonymous session flow"
```

---

## Task 15: Manual E2E Testing

### Step 1: Start dev server

Run: `python main.py --dev`

### Step 2: Test anonymous flow

1. Open http://localhost:5173 in incognito/private window
2. Click "Start Learning"
3. Chat briefly with AI tutor
4. Click "Done" on article stage
5. Verify auth prompt appears
6. Click "Sign in with Discord"
7. Complete OAuth
8. Verify you return to lesson with progress preserved
9. Complete lesson
10. Verify completion modal shows with signup CTA

### Step 3: Test direct signup flow

1. Open http://localhost:5173
2. Click "Sign Up"
3. Verify you go to signup wizard

---

## Summary

After all tasks:
- Anonymous users can start lessons without auth
- Sessions stored in localStorage + DB with `user_id = NULL`
- Auth prompt appears after first content stage
- `/api/lesson-sessions/{id}/claim` assigns session to user
- Homepage has both "Start Learning" and "Sign Up" buttons
- Completion modal directs to signup wizard

**Backend TDD coverage:**
- `claim_session` function
- Anonymous session creation
- Session access control
- Claim endpoint

**Frontend integration test coverage:**
- Anonymous session creation + localStorage
- Session claiming after auth
- Auth prompt trigger
