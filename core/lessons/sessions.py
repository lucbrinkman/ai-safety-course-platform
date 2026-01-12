"""Lesson session management - database operations."""

from datetime import datetime, timezone

from sqlalchemy import select, update, insert

from core.database import get_connection, get_transaction
from core.tables import lesson_sessions


class SessionNotFoundError(Exception):
    """Raised when a session cannot be found."""
    pass


class SessionAlreadyClaimedError(Exception):
    """Raised when trying to claim a session that already has a user."""
    pass


async def create_session(user_id: int | None, lesson_slug: str) -> dict:
    """
    Create a new lesson session.

    Args:
        user_id: The user's database ID
        lesson_slug: The lesson slug to start

    Returns:
        Dict with session data including session_id
    """
    async with get_transaction() as conn:
        result = await conn.execute(
            insert(lesson_sessions)
            .values(
                user_id=user_id,
                lesson_slug=lesson_slug,
                current_stage_index=0,
                messages=[],
            )
            .returning(lesson_sessions)
        )
        row = result.mappings().one()
        return dict(row)


async def get_session(session_id: int) -> dict:
    """
    Get a session by ID.

    Args:
        session_id: The session ID

    Returns:
        Dict with session data

    Raises:
        SessionNotFoundError: If session doesn't exist
    """
    async with get_connection() as conn:
        result = await conn.execute(
            select(lesson_sessions).where(lesson_sessions.c.session_id == session_id)
        )
        row = result.mappings().first()

        if not row:
            raise SessionNotFoundError(f"Session not found: {session_id}")

        return dict(row)


async def get_user_sessions(user_id: int) -> list[dict]:
    """
    Get all sessions for a user.

    Args:
        user_id: The user's database ID

    Returns:
        List of session dicts
    """
    async with get_connection() as conn:
        result = await conn.execute(
            select(lesson_sessions)
            .where(lesson_sessions.c.user_id == user_id)
            .order_by(lesson_sessions.c.last_active_at.desc())
        )
        return [dict(row) for row in result.mappings().all()]


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


async def get_user_lesson_progress(user_id: int | None) -> dict[str, dict]:
    """
    Get progress for all lessons a user has started.

    Args:
        user_id: The user's database ID (None for anonymous)

    Returns:
        Dict mapping lesson_slug to progress info:
        {
            "lesson-slug": {
                "status": "completed" | "in_progress" | "not_started",
                "current_stage_index": int | None,
                "session_id": int | None,
            }
        }
    """
    if user_id is None:
        return {}

    async with get_connection() as conn:
        result = await conn.execute(
            select(lesson_sessions)
            .where(lesson_sessions.c.user_id == user_id)
            .order_by(lesson_sessions.c.last_active_at.desc())
        )
        rows = result.mappings().all()

    progress = {}
    for row in rows:
        lesson_slug = row["lesson_slug"]
        # Only keep the most recent session per lesson
        if lesson_slug not in progress:
            if row["completed_at"] is not None:
                status = "completed"
            else:
                status = "in_progress"
            progress[lesson_slug] = {
                "status": status,
                "current_stage_index": row["current_stage_index"],
                "session_id": row["session_id"],
            }
    return progress
