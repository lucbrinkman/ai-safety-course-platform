"""
Unified backend entry point.

Architecture:
- One Python process, one asyncio event loop
- Three peer services running concurrently:
  1. FastAPI (HTTP server for web frontend)
  2. Discord bot (WebSocket connection to Discord)
  3. [Future: Scheduler for background tasks like meeting reminders]

We use FastAPI's lifespan to manage startup/shutdown, but at runtime
all services are equal peers in the event loop. The lifespan pattern
gives us uvicorn's signal handling and --reload for free.

Run with: python main.py
"""

import asyncio
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Set up import paths before any local imports
# This allows discord_bot cogs to use their relative imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
# Append (not insert at 0) to allow cog loading without shadowing root main.py
sys.path.append(str(project_root / "discord_bot"))

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Import bot from discord_bot module
from discord_bot.main import bot

# Import routes using full paths (don't add web_api to sys.path to avoid main.py conflict)
from web_api.routes.auth import router as auth_router
from web_api.routes.users import router as users_router

# Track bot task for cleanup
_bot_task: asyncio.Task | None = None


async def start_bot():
    """
    Start Discord bot (non-blocking).

    Uses bot.start() instead of bot.run() so it can run
    alongside FastAPI in the same event loop.
    """
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        print("Warning: DISCORD_BOT_TOKEN not set, Discord bot will not start")
        return

    try:
        await bot.start(token)
    except Exception as e:
        print(f"Discord bot error: {e}")
        raise


async def stop_bot():
    """Stop Discord bot gracefully."""
    if bot and not bot.is_closed():
        await bot.close()
        print("Discord bot stopped")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.

    Starts peer services (Discord bot, future scheduler) as background tasks.
    They run concurrently with FastAPI in the same event loop.
    """
    global _bot_task

    # Start peer services as background tasks
    print("Starting Discord bot...")
    _bot_task = asyncio.create_task(start_bot())
    # Future: scheduler_task = asyncio.create_task(start_scheduler())

    yield  # FastAPI runs here, bot runs alongside it

    # Graceful shutdown of all peer services
    print("Shutting down peer services...")
    await stop_bot()
    if _bot_task:
        _bot_task.cancel()
        try:
            await _bot_task
        except asyncio.CancelledError:
            pass


# Create FastAPI app with lifespan
app = FastAPI(
    title="AI Safety Course Platform API",
    lifespan=lifespan,
)

# CORS configuration
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(users_router)


@app.get("/")
async def root():
    """Serve landing page if it exists, otherwise return API status."""
    landing_path = project_root / "static" / "landing.html"
    if landing_path.exists():
        return FileResponse(landing_path)
    return {
        "status": "ok",
        "bot_ready": bot.is_ready() if bot else False,
    }


@app.get("/api/status")
async def api_status():
    """API status endpoint (moved from /)."""
    return {
        "status": "ok",
        "bot_ready": bot.is_ready() if bot else False,
    }


@app.get("/health")
async def health():
    """Health check endpoint with detailed status."""
    return {
        "status": "healthy",
        "bot_connected": bot.is_ready() if bot else False,
        "bot_latency_ms": round(bot.latency * 1000) if bot and bot.is_ready() else None,
    }


# SPA routes - serve React app for frontend routes (only if built SPA exists)
spa_path = project_root / "static" / "spa"
if spa_path.exists():
    @app.get("/signup")
    @app.get("/auth/code")
    async def spa():
        """Serve React SPA for frontend routes."""
        return FileResponse(spa_path / "index.html")

    # Mount static assets from built SPA
    assets_path = spa_path / "assets"
    if assets_path.exists():
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")


if __name__ == "__main__":
    import uvicorn

    # Run with uvicorn
    # Note: --reload may cause issues with Discord bot reconnecting frequently
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.environ.get("ENV") == "development",
    )
