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
