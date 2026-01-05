# Onboarding: Lesson-First Flow Design

**Date:** 2026-01-05
**Status:** Approved

## Overview

Add a "Start Learning" path alongside the existing "Sign Up" button on the homepage. Users can try the intro lesson anonymously before committing to signup.

## User Flows

### Flow A: Direct Signup (Existing)
```
Homepage → "Sign Up" → /signup (3-step wizard) → Enrolled
```

### Flow B: Lesson First (New)
```
Homepage → "Start Learning" → /lesson/intelligence-feedback-loop (anonymous)
    ├── Stage 1: Chat with AI tutor
    ├── Stage 2: Read article
    └── Click "Done" on article
            ↓
        Auth Prompt Modal: "Sign in with Discord to save progress"
            ↓
        Discord OAuth → Session claimed to user
            ↓
        Continue lesson (authenticated, progress saved)
            └── Lesson complete
                    ↓
                Completion Modal → "Join the Full Course" button
                    ↓
                /signup (same 3-step wizard)
```

## Design Decisions

| Decision | Choice |
|----------|--------|
| Intro lesson | `intelligence-feedback-loop` (existing) |
| Auth prompt trigger | After completing first non-chat stage (article) |
| Anonymous session storage | DB immediately with `user_id = NULL` |
| Session persistence | Session ID in localStorage |
| Post-auth behavior | Claim existing session via new endpoint |
| Post-lesson action | Completion modal with signup link |
| Signup wizard | Full 3-step wizard (same as direct signup) |

## Frontend Changes

### Homepage (`/`)
- Keep "Sign Up" button → navigates to `/signup`
- Add "Start Learning" button → navigates to `/lesson/intelligence-feedback-loop`

### Lesson UI (`UnifiedLesson.tsx`)
Add persistent auth status indicator:
- **Anonymous:** Banner/chip showing "Login to save your progress" with Discord sign-in link
- **Authenticated:** Shows Discord username (subtle, non-intrusive)

### Auth Prompt Modal (New Component)
- Triggered when anonymous user clicks "Done" on first non-chat stage
- Content: "Sign in with Discord to save your progress"
- Single button: "Sign in with Discord" → initiates OAuth flow
- On OAuth return: calls `/api/lesson-sessions/{id}/claim`, continues lesson

### Completion Modal (New Component)
- Triggered when lesson `completed_at` is set
- Content: "🎉 You finished the intro lesson!"
- CTA button: "Join the Full Course" → navigates to `/signup`
- Dismiss option for users not ready to commit

## Backend Changes

### Database
Make `user_id` nullable in `lesson_sessions` table:
```sql
ALTER TABLE lesson_sessions ALTER COLUMN user_id DROP NOT NULL;
```

### New Endpoint: Claim Session
```
POST /api/lesson-sessions/{session_id}/claim
```

**Auth:** Required (must be logged in)

**Behavior:**
1. Verify session exists
2. Verify session has `user_id = NULL` (unclaimed)
3. Set `user_id` to authenticated user's ID
4. Return success

**Response:** `{"claimed": true}`

**Errors:**
- 404: Session not found
- 403: Session already claimed

### Modified: Create Session
```
POST /api/lesson-sessions
```

**Change:** Allow creation without authentication
- If authenticated: `user_id` = current user
- If anonymous: `user_id` = NULL

### Modified: Session Access
Allow access to unclaimed sessions by session ID (for anonymous users continuing their session).

## Data Flow

### Anonymous User Starts Lesson
1. User clicks "Start Learning" on homepage
2. Frontend navigates to `/lesson/intelligence-feedback-loop`
3. Frontend checks localStorage for existing `sessionId`
4. If none: `POST /api/lesson-sessions` with `lesson_id`
5. Backend creates session with `user_id = NULL`, returns `session_id`
6. Frontend stores `session_id` in localStorage
7. User interacts with lesson, messages saved to DB immediately

### Anonymous User Authenticates
1. User completes article stage, clicks "Done"
2. Auth Prompt Modal appears
3. User clicks "Sign in with Discord"
4. OAuth flow: `/auth/discord` → Discord → callback → JWT cookie set
5. Redirect back to `/lesson/intelligence-feedback-loop?claimed=pending`
6. Frontend detects auth + has `sessionId` in localStorage
7. `POST /api/lesson-sessions/{sessionId}/claim`
8. Session now belongs to user, continue lesson normally

### User Completes Lesson
1. User advances through remaining stages
2. Final stage completed → `completed_at` set
3. Completion Modal appears
4. User clicks "Join the Full Course"
5. Navigate to `/signup`

## Security Considerations

**Session Claiming:**
- Session IDs are random integers, hard to guess
- Window of vulnerability is short (anonymous → auth)
- Low stakes (only lesson progress, not sensitive data)
- Could add rate limiting on claim endpoint if needed

**Anonymous Sessions:**
- Will accumulate unclaimed sessions over time
- Consider cleanup job for sessions with `user_id = NULL` older than X days

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| User closes browser, returns later | localStorage has `sessionId`, resumes session |
| User clears storage | Starts fresh (acceptable for anonymous) |
| User already logged in clicks "Start Learning" | Creates session with their `user_id` immediately, no claim needed |
| User tries to claim already-claimed session | 403 error, frontend handles gracefully |
| Multiple tabs | Both use same localStorage `sessionId` |

## Implementation Order

1. **Database:** Make `user_id` nullable
2. **Backend:** Add claim endpoint
3. **Backend:** Allow anonymous session creation
4. **Frontend:** Add localStorage session tracking for anonymous users
5. **Frontend:** Auth status indicator in lesson UI
6. **Frontend:** Auth Prompt Modal
7. **Frontend:** Completion Modal
8. **Frontend:** Homepage dual buttons

## Out of Scope (Future)

- Smart routing for logged-in users who already completed intro
- Progress dashboard showing completed lessons
- Multiple intro lesson options
- Cleanup job for orphaned anonymous sessions
