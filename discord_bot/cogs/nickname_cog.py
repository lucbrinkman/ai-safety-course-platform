"""
Nickname Cog - Syncs display name between web signup and Discord server nickname.

Discord is the source of truth. Database is a cached copy to avoid API rate limits.
"""

import discord
from discord.ext import commands

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core import get_user_nickname, update_user_nickname


# Module-level reference to bot, set during cog setup
_bot = None


async def update_nickname_in_discord(discord_id: str, nickname: str | None) -> bool:
    """
    Update user's nickname in Discord server(s) if they're a member.
    Called by web API via core.nickname_sync wrapper.

    Returns True if nickname was updated in at least one guild.
    """
    if _bot is None or not _bot.is_ready():
        return False

    user_id = int(discord_id)
    updated = False

    for guild in _bot.guilds:
        try:
            member = guild.get_member(user_id)
            if not member:
                try:
                    member = await guild.fetch_member(user_id)
                except discord.NotFound:
                    continue

            await member.edit(nick=nickname)
            updated = True
        except discord.Forbidden:
            pass
        except discord.HTTPException:
            pass

    return updated


class NicknameCog(commands.Cog):
    """Cog for syncing nicknames between web signup and Discord."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Apply stored display name when user joins (if they have no nickname set)."""
        if member.nick:
            return  # User already has a nickname, don't override

        discord_id = str(member.id)

        # Look up user nickname via core function
        nickname = await get_user_nickname(discord_id)

        if not nickname:
            return  # No stored name

        # Apply stored name as nickname
        try:
            await member.edit(nick=nickname)
        except discord.Forbidden:
            pass  # Silently fail if we can't set nickname

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Sync nickname changes from Discord to database."""
        # Only care about nickname changes
        if before.nick == after.nick:
            return

        discord_id = str(after.id)
        # If nickname deleted, fall back to Discord username
        new_name = after.nick if after.nick else after.name

        # Update database to match Discord via core function
        await update_user_nickname(discord_id, new_name)


async def setup(bot):
    global _bot
    _bot = bot
    await bot.add_cog(NicknameCog(bot))
