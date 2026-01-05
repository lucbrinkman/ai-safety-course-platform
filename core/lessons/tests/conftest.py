"""Pytest fixtures for lesson tests."""

import uuid
import pytest
import pytest_asyncio
from sqlalchemy import text
from dotenv import load_dotenv

# Load env vars at module import time
load_dotenv('.env.local')


@pytest_asyncio.fixture(autouse=True)
async def cleanup_engine():
    """Clean up the database engine after each test to avoid connection pool issues."""
    yield
    from core.database import close_engine
    await close_engine()


@pytest_asyncio.fixture
async def test_user_id():
    """Create a test user and return their user_id. Cleans up after test."""
    from core.database import get_transaction

    unique_id = str(uuid.uuid4())[:8]
    discord_id = f"test_{unique_id}"

    async with get_transaction() as conn:
        result = await conn.execute(
            text("""
                INSERT INTO users (discord_id, discord_username)
                VALUES (:discord_id, :username)
                RETURNING user_id
            """),
            {"discord_id": discord_id, "username": f"test_user_{unique_id}"}
        )
        row = result.fetchone()
        user_id = row[0]

    yield user_id

    # Cleanup: delete the test user (cascades to lesson_sessions)
    async with get_transaction() as conn:
        await conn.execute(
            text("DELETE FROM users WHERE user_id = :user_id"),
            {"user_id": user_id}
        )


@pytest_asyncio.fixture
async def another_test_user_id():
    """Create another test user and return their user_id. Cleans up after test."""
    from core.database import get_transaction

    unique_id = str(uuid.uuid4())[:8]
    discord_id = f"another_test_{unique_id}"

    async with get_transaction() as conn:
        result = await conn.execute(
            text("""
                INSERT INTO users (discord_id, discord_username)
                VALUES (:discord_id, :username)
                RETURNING user_id
            """),
            {"discord_id": discord_id, "username": f"another_test_user_{unique_id}"}
        )
        row = result.fetchone()
        user_id = row[0]

    yield user_id

    # Cleanup: delete the test user (cascades to lesson_sessions)
    async with get_transaction() as conn:
        await conn.execute(
            text("DELETE FROM users WHERE user_id = :user_id"),
            {"user_id": user_id}
        )
