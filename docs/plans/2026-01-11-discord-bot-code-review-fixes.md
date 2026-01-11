# Discord Bot Code Review Fixes

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix remaining code quality issues from Discord bot code review (DRY violations, misplaced imports, exception handling).

**Architecture:** Apply DRY principle by extracting helper methods for repeated patterns. Move imports to module level. Improve exception logging without breaking functionality.

**Tech Stack:** Python, discord.py

---

## Status from Code Review

Based on analysis, the following issues remain unfixed:

| # | Issue | File | Priority |
|---|-------|------|----------|
| 1 | DRY: Duplicate URL construction | enrollment_cog.py | Important |
| 2 | DRY: Duplicate channel permission code | groups_cog.py | Important |
| 3 | DRY: Duplicate interaction response pattern | breakout_cog.py | Important |
| 4 | Swallowed exceptions in progress callback | scheduler_cog.py | Important |
| 5 | `import io` inside functions | ping_cog.py | Minor |
| 6 | `import re` in wrong location | stampy_cog.py | Minor |

Note: All bare `except:` clauses have already been fixed by other sessions.

---

## Task 1: Fix DRY Violation in enrollment_cog.py

**Files:**
- Modify: `discord_bot/cogs/enrollment_cog.py:37-52`

**Step 1: Add helper function after the imports**

Add this function right after the imports (before the class definition):

```python
def _build_auth_link(code: str, next_path: str) -> str:
    """Build an authenticated web link with the given auth code and redirect path."""
    web_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    return f"{web_url}/auth/code?code={code}&next={next_path}"
```

**Step 2: Update signup command**

Change lines 37-38 from:

```python
        web_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
        link = f"{web_url}/auth/code?code={code}&next=/signup"
```

To:

```python
        link = _build_auth_link(code, "/signup")
```

**Step 3: Update availability command**

Change lines 51-52 from:

```python
        web_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
        link = f"{web_url}/auth/code?code={code}&next=/availability"
```

To:

```python
        link = _build_auth_link(code, "/availability")
```

**Step 4: Verify no regressions**

Run: `python -c "from discord_bot.cogs.enrollment_cog import EnrollmentCog; print('Import OK')"`
Expected: No errors

---

## Task 2: Fix DRY Violation in groups_cog.py

**Files:**
- Modify: `discord_bot/cogs/groups_cog.py`

**Step 1: Add helper method to GroupsCog class**

Add this method after `__init__`:

```python
    async def _grant_channel_permissions(
        self,
        member: discord.Member,
        text_channel: discord.TextChannel,
        voice_channel: discord.VoiceChannel,
    ):
        """Grant standard group channel permissions to a member."""
        await text_channel.set_permissions(
            member,
            view_channel=True,
            send_messages=True,
            read_message_history=True,
        )
        await voice_channel.set_permissions(
            member,
            view_channel=True,
            connect=True,
            speak=True,
        )
```

**Step 2: Update realize_groups to use helper**

Replace the permission-setting block (around lines 131-144) from:

```python
                        await text_channel.set_permissions(
                            member,
                            view_channel=True,
                            send_messages=True,
                            read_message_history=True,
                        )
                        await voice_channel.set_permissions(
                            member,
                            view_channel=True,
                            connect=True,
                            speak=True,
                        )
```

To:

```python
                        await self._grant_channel_permissions(
                            member, text_channel, voice_channel
                        )
```

**Step 3: Update on_member_join to use helper**

Replace the permission-setting block (around lines 367-378) from:

```python
                if text_channel:
                    await text_channel.set_permissions(
                        member,
                        view_channel=True,
                        send_messages=True,
                        read_message_history=True,
                    )
                if voice_channel:
                    await voice_channel.set_permissions(
                        member,
                        view_channel=True,
                        connect=True,
                        speak=True,
                    )
```

To:

```python
                if text_channel and voice_channel:
                    await self._grant_channel_permissions(
                        member, text_channel, voice_channel
                    )
```

**Step 4: Verify no regressions**

Run: `python -c "from discord_bot.cogs.groups_cog import GroupsCog; print('Import OK')"`
Expected: No errors

---

## Task 3: Fix DRY Violation in breakout_cog.py

**Files:**
- Modify: `discord_bot/cogs/breakout_cog.py`

**Step 1: Add helper method to BreakoutCog class**

Add this method after `__init__`:

```python
    async def _send_response(
        self,
        interaction: discord.Interaction,
        content: str,
        ephemeral: bool = True,
    ):
        """Send a response, using followup if the interaction was already responded to."""
        if interaction.response.is_done():
            await interaction.followup.send(content, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(content, ephemeral=ephemeral)
```

**Step 2: Update run_breakout to use helper**

Replace the repeated pattern at lines 91-94:

```python
        if interaction.response.is_done():
            await interaction.followup.send("You must be in a voice channel.", ephemeral=True)
        else:
            await interaction.response.send_message("You must be in a voice channel.", ephemeral=True)
```

With:

```python
        await self._send_response(interaction, "You must be in a voice channel.")
```

**Step 3: Continue replacing pattern at lines 101-104**

Replace:

```python
        if interaction.response.is_done():
            await interaction.followup.send("A breakout session is already active. Use `/collect` first.", ephemeral=True)
        else:
            await interaction.response.send_message("A breakout session is already active. Use `/collect` first.", ephemeral=True)
```

With:

```python
        await self._send_response(
            interaction,
            "A breakout session is already active. Use `/collect` first."
        )
```

**Step 4: Replace pattern at lines 114-117**

Replace:

```python
        if interaction.response.is_done():
            await interaction.followup.send("There are no other users in the voice channel to split.", ephemeral=True)
        else:
            await interaction.response.send_message("There are no other users in the voice channel to split.", ephemeral=True)
```

With:

```python
        await self._send_response(
            interaction,
            "There are no other users in the voice channel to split."
        )
```

**Step 5: Replace pattern in run_collect at lines 242-245**

Replace:

```python
        if interaction.response.is_done():
            await interaction.followup.send("No active breakout session to collect.", ephemeral=True)
        else:
            await interaction.response.send_message("No active breakout session to collect.", ephemeral=True)
```

With:

```python
        await self._send_response(
            interaction,
            "No active breakout session to collect."
        )
```

**Step 6: Verify no regressions**

Run: `python -c "from discord_bot.cogs.breakout_cog import BreakoutCog; print('Import OK')"`
Expected: No errors

---

## Task 4: Improve Exception Handling in scheduler_cog.py

**Files:**
- Modify: `discord_bot/cogs/scheduler_cog.py:78-86`

The current code swallows ALL exceptions, which could hide important errors:

```python
async def update_progress(current, total, best_score, total_people):
    try:
        await progress_msg.edit(...)
    except Exception:
        pass
```

**Step 1: Replace broad exception with specific handling**

Change lines 78-86 from:

```python
        async def update_progress(current, total, best_score, total_people):
            try:
                await progress_msg.edit(
                    content=f"Scheduling...\n"
                            f"Iteration: {current}/{total} | "
                            f"Best: {best_score}/{total_people}"
                )
            except Exception:
                pass
```

To:

```python
        async def update_progress(current, total, best_score, total_people):
            try:
                await progress_msg.edit(
                    content=f"Scheduling...\n"
                            f"Iteration: {current}/{total} | "
                            f"Best: {best_score}/{total_people}"
                )
            except discord.HTTPException:
                pass  # Rate limited or message deleted, expected
            except Exception as e:
                print(f"[SchedulerCog] Progress update failed: {e}")
```

**Step 2: Verify no regressions**

Run: `python -c "from discord_bot.cogs.scheduler_cog import SchedulerCog; print('Import OK')"`
Expected: No errors

---

## Task 5: Move Import to Module Level in ping_cog.py

**Files:**
- Modify: `discord_bot/cogs/ping_cog.py`

The `import io` statement appears inside functions at lines 79 and 618.

**Step 1: Add import to top of file**

After line 10 (`import asyncio`), add:

```python
import io
```

**Step 2: Remove import from txt_test function**

Remove line 79:

```python
        import io
```

**Step 3: Remove import from toggle_button method in CoTExpandView**

Remove line 618:

```python
            import io
```

**Step 4: Verify no regressions**

Run: `python -c "from discord_bot.cogs.ping_cog import PingCog; print('Import OK')"`
Expected: No errors

---

## Task 6: Move Import to Module Level in stampy_cog.py

**Files:**
- Modify: `discord_bot/cogs/stampy_cog.py`

The `import re` statement is at line 61, after some function definitions.

**Step 1: Move import to top of file**

After line 12 (`import os`), add:

```python
import re
```

**Step 2: Remove misplaced import**

Remove line 61:

```python
import re
```

**Step 3: Verify no regressions**

Run: `python -c "from discord_bot.cogs.stampy_cog import StampyCog; print('Import OK')"`
Expected: No errors

---

## Final Verification

After all tasks complete:

1. Run all Discord bot tests:
   ```bash
   pytest discord_bot/tests/ -v
   ```

2. Verify all cogs load correctly:
   ```bash
   python -c "
   from discord_bot.cogs import enrollment_cog, groups_cog, breakout_cog, scheduler_cog, ping_cog, stampy_cog
   print('All cogs import successfully')
   "
   ```

---

## Summary

| Task | Description | Estimated Changes |
|------|-------------|-------------------|
| 1 | DRY: URL construction helper | +5 lines, -4 lines |
| 2 | DRY: Channel permissions helper | +15 lines, -22 lines |
| 3 | DRY: Response helper | +10 lines, -16 lines |
| 4 | Better exception handling | +2 lines |
| 5 | Move `import io` | +1 line, -2 lines |
| 6 | Move `import re` | +1 line, -1 line |
