# Architecture Code Review Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix remaining architecture issues from code review 05-architecture.md

**Architecture:** Create a centralized config module in core/ to eliminate duplicate configuration across main.py and web_api/routes/auth.py. Refactor nickname_sync.py to use a callback registration pattern instead of fragile sys.modules lookup. Clean up dead test file.

**Tech Stack:** Python, FastAPI, discord.py

---

## Status Summary

**Already Fixed (verified 2026-01-11):**
- Issue 1: `web_api/main.py` dead code - File already deleted
- Issue 3: Session cookie `secure=False` - Fixed with `is_production` check in `web_api/auth.py:76`
- Issue 4: OAuth state memory leak - Fixed with TTL cleanup in `web_api/routes/auth.py:86-92`
- Bare `except:` in `groups_cog.py` - Already fixed

**Remaining Issues:**
1. Issue 6 (Important): `core/nickname_sync.py` uses fragile `sys.modules` lookup
2. Issue 9 (Minor): Repeated `DEV_MODE` check pattern across files
3. Issue 10 (Minor): Duplicate CORS allowed origins in `main.py` and `auth.py`
4. Issue 5 (Minor): `test_stampy_stream.py` in project root

**Skipped (low priority / design decisions):**
- Issue 2: Duplicate argument parsing - intentional (early parse needed before imports)
- Issue 7: `sys.path` manipulation - requires pyproject.toml migration (larger change)
- Issue 8: Version pinning - project choice, not a bug

---

## Task 1: Create Centralized Config Module

**Files:**
- Create: `core/config.py`
- Modify: `core/__init__.py`

**Step 1: Create the config module**

Create `core/config.py` with centralized configuration helpers:

```python
"""
Centralized configuration for the AI Safety Course Platform.

Provides environment-aware settings and eliminates duplicate config
logic across main.py and web_api/routes/auth.py.
"""

import os


def is_dev_mode() -> bool:
    """Check if running in development mode (--dev flag or DEV_MODE env)."""
    return os.getenv("DEV_MODE", "").lower() in ("true", "1", "yes")


def is_production() -> bool:
    """Check if running on Railway (production environment)."""
    return bool(os.environ.get("RAILWAY_ENVIRONMENT"))


def get_api_port() -> int:
    """Get API server port from env or default."""
    return int(os.getenv("API_PORT", "8000"))


def get_vite_port() -> int:
    """Get Vite dev server port from env or default."""
    return int(os.getenv("VITE_PORT", "5173"))


def get_frontend_url() -> str:
    """Get frontend URL based on mode."""
    if is_dev_mode():
        return f"http://localhost:{get_vite_port()}"
    if is_production():
        return os.environ.get("FRONTEND_URL", f"http://localhost:{get_api_port()}")
    return f"http://localhost:{get_api_port()}"


def get_allowed_origins() -> list[str]:
    """
    Get list of allowed CORS origins.

    Includes localhost variants for dev and the production frontend URL.
    """
    origins = [
        "http://localhost:5173",
        "http://localhost:8000",
        "http://localhost:8001",
        "http://localhost:8002",
        "http://localhost:8003",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8001",
        "http://127.0.0.1:8002",
        "http://127.0.0.1:8003",
    ]

    # Add production frontend URL if not already in list
    frontend_url = get_frontend_url()
    if frontend_url not in origins:
        origins.append(frontend_url)

    # Add explicit FRONTEND_URL env var if set
    env_frontend = os.environ.get("FRONTEND_URL")
    if env_frontend and env_frontend not in origins:
        origins.append(env_frontend)

    return origins
```

**Step 2: Export from core/__init__.py**

Add to the existing exports in `core/__init__.py`:

```python
from .config import (
    is_dev_mode,
    is_production,
    get_api_port,
    get_vite_port,
    get_frontend_url,
    get_allowed_origins,
)
```

**Step 3: Verify module loads**

Run: `python -c "from core import is_dev_mode, get_allowed_origins; print('OK')"`
Expected: `OK`

**Step 4: Commit**

```bash
jj describe -m "feat(core): add centralized config module

Addresses code review Issue 9 and 10:
- Centralize DEV_MODE check pattern
- Centralize CORS allowed origins

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 2: Update main.py to Use Centralized Config

**Files:**
- Modify: `main.py:217-238` (CORS configuration)
- Modify: `main.py:258,294` (DEV_MODE checks)

**Step 1: Update CORS configuration**

Replace the hardcoded origins list in `main.py` (lines 217-238) with:

```python
from core import get_allowed_origins, get_frontend_url

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Step 2: Update DEV_MODE checks**

Replace inline DEV_MODE checks with `is_dev_mode()`:

Line 258 (root endpoint):
```python
from core import is_dev_mode

# In root() function:
if is_dev_mode():
```

Line 294 (SPA routes):
```python
if spa_path.exists() and not is_dev_mode():
```

**Step 3: Run server to verify**

Run: `python main.py --dev --port 8099 --no-bot &`
Expected: Server starts without errors
Clean up: `lsof -ti:8099 | xargs kill`

**Step 4: Commit**

```bash
jj describe -m "refactor(main): use centralized config for CORS and DEV_MODE

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 3: Update web_api/routes/auth.py to Use Centralized Config

**Files:**
- Modify: `web_api/routes/auth.py:37-70` (config and ALLOWED_ORIGINS)

**Step 1: Replace inline config with imports**

At the top of the file, add import:
```python
from core import is_dev_mode, is_production, get_api_port, get_vite_port, get_frontend_url, get_allowed_origins
```

**Step 2: Simplify URL computation**

Replace lines 33-70 with:

```python
# Compute URLs based on mode - using centralized config
_api_port = get_api_port()
_vite_port = get_vite_port()

if is_dev_mode():
    DISCORD_REDIRECT_URI = f"http://localhost:{_api_port}/auth/discord/callback"
    FRONTEND_URL = f"http://localhost:{_vite_port}"
elif is_production():
    DISCORD_REDIRECT_URI = os.environ.get("DISCORD_REDIRECT_URI", f"http://localhost:{_api_port}/auth/discord/callback")
    FRONTEND_URL = os.environ.get("FRONTEND_URL", f"http://localhost:{_api_port}")
else:
    DISCORD_REDIRECT_URI = f"http://localhost:{_api_port}/auth/discord/callback"
    FRONTEND_URL = f"http://localhost:{_api_port}"

# Use centralized allowed origins
ALLOWED_ORIGINS = get_allowed_origins()
```

**Step 3: Remove redundant variables**

Remove these lines (now handled by centralized config):
```python
_dev_mode = os.environ.get("DEV_MODE", "").lower() in ("true", "1", "yes")
_is_railway = bool(os.environ.get("RAILWAY_ENVIRONMENT"))
```

**Step 4: Run tests**

Run: `python -c "from web_api.routes.auth import ALLOWED_ORIGINS; print(ALLOWED_ORIGINS)"`
Expected: List of origins printed

**Step 5: Commit**

```bash
jj describe -m "refactor(auth): use centralized config for origins and mode checks

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 4: Refactor nickname_sync.py to Use Callback Pattern

**Files:**
- Modify: `core/nickname_sync.py`
- Modify: `discord_bot/cogs/nickname_cog.py:94-97` (setup function)

This is the most important fix - eliminates the fragile `sys.modules` lookup that violates layer separation.

**Step 1: Rewrite nickname_sync.py with callback registration**

Replace entire contents of `core/nickname_sync.py`:

```python
"""
Nickname sync - bridges web API and Discord bot for nickname updates.

Uses callback registration pattern so:
1. core/ has no imports from discord_bot/
2. discord_bot/ registers its implementation at startup
3. web_api/ calls through core/ without knowing about Discord

This maintains the 3-layer architecture documented in CLAUDE.md.
"""

from typing import Callable, Awaitable

# Type for the nickname update callback
NicknameUpdateCallback = Callable[[str, str | None], Awaitable[bool]]

# Registered callback - set by discord_bot at startup
_nickname_callback: NicknameUpdateCallback | None = None


def register_nickname_callback(callback: NicknameUpdateCallback) -> None:
    """
    Register the Discord nickname update callback.

    Called by discord_bot/cogs/nickname_cog.py during setup.
    """
    global _nickname_callback
    _nickname_callback = callback


def unregister_nickname_callback() -> None:
    """
    Unregister the callback (for testing or bot shutdown).
    """
    global _nickname_callback
    _nickname_callback = None


async def update_nickname_in_discord(discord_id: str, nickname: str | None) -> bool:
    """
    Update user's nickname in Discord.

    Delegates to the registered callback from discord_bot.
    Returns False if no callback is registered (bot not running).
    """
    if _nickname_callback is None:
        print("[nickname_sync] No callback registered (bot not running?)")
        return False

    return await _nickname_callback(discord_id, nickname)


__all__ = [
    "register_nickname_callback",
    "unregister_nickname_callback",
    "update_nickname_in_discord",
]
```

**Step 2: Update nickname_cog.py to register callback**

Modify `discord_bot/cogs/nickname_cog.py` setup function (lines 94-97):

```python
async def setup(bot):
    global _bot
    _bot = bot

    # Register the callback with core so web API can trigger nickname updates
    from core.nickname_sync import register_nickname_callback
    register_nickname_callback(update_nickname_in_discord)

    await bot.add_cog(NicknameCog(bot))
```

**Step 3: Export new functions from core/__init__.py**

Add to exports:
```python
from .nickname_sync import (
    register_nickname_callback,
    unregister_nickname_callback,
    update_nickname_in_discord,
)
```

**Step 4: Verify the refactor**

Run: `python -c "from core import register_nickname_callback, update_nickname_in_discord; print('OK')"`
Expected: `OK`

**Step 5: Commit**

```bash
jj describe -m "refactor(nickname_sync): replace sys.modules with callback pattern

Addresses code review Issue 6 (Important):
- Eliminates fragile sys.modules lookup
- Discord bot registers callback at startup
- Maintains clean 3-layer architecture

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 5: Remove Dead Test File

**Files:**
- Delete: `test_stampy_stream.py`

**Step 1: Verify file is not imported anywhere**

Run: `grep -r "test_stampy_stream" --include="*.py" .`
Expected: No matches (or only in the file itself)

**Step 2: Delete the file**

Run: `rm test_stampy_stream.py`

**Step 3: Verify deletion**

Run: `ls test_stampy_stream.py`
Expected: "No such file or directory"

**Step 4: Commit**

```bash
jj describe -m "chore: remove test_stampy_stream.py from project root

Dead code - standalone test/debug script no longer needed.
Addresses code review Issue 5.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 6: Final Verification

**Step 1: Run the test suite**

Run: `pytest discord_bot/tests/ -v`
Expected: All tests pass

**Step 2: Start server and verify**

Run: `python main.py --dev --port 8099 --no-bot &`
Expected: Server starts without errors

Run: `curl -s http://localhost:8099/api/status | jq`
Expected: `{"status": "ok", ...}`

Clean up: `lsof -ti:8099 | xargs kill`

**Step 3: Squash commits if needed**

Run: `jj log --limit 6` to review commits
If multiple WIP commits, squash them appropriately

---

## Summary of Changes

| Issue | File(s) | Change |
|-------|---------|--------|
| 9, 10 | `core/config.py` (new) | Centralized config helpers |
| 9, 10 | `main.py` | Use centralized CORS and DEV_MODE |
| 9, 10 | `web_api/routes/auth.py` | Use centralized ALLOWED_ORIGINS |
| 6 | `core/nickname_sync.py` | Callback pattern instead of sys.modules |
| 6 | `discord_bot/cogs/nickname_cog.py` | Register callback at setup |
| 5 | `test_stampy_stream.py` | Deleted |

**Total: 6 files changed, 1 file deleted, 1 file created**
