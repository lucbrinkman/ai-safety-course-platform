"""
Stampy Discord cog.
"""
import discord
from discord.ext import commands
import traceback

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core import stampy

ASK_STAMPY_CHANNEL = "ask-stampy"
STAMPY_NAME = "Stampy"
STAMPY_AVATAR = "https://stampy.ai/images/stampy-logo.png"


def format_thinking(text: str, prefix: str = "*Thinking...*") -> str:
    """Format thinking text with quote+subtext styling."""
    lines = text.split('\n')
    formatted = '\n'.join(f'> -# {line}' if line.strip() else '> ' for line in lines)
    return f"{prefix}\n{formatted}"


class StampyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._webhooks: dict[int, discord.Webhook] = {}

    async def _get_webhook(self, channel: discord.TextChannel) -> discord.Webhook:
        """Get or create a webhook for the channel."""
        print(f"[Stampy] Getting webhook for channel {channel.name} ({channel.id})")

        if channel.id in self._webhooks:
            print(f"[Stampy] Using cached webhook")
            return self._webhooks[channel.id]

        try:
            webhooks = await channel.webhooks()
            print(f"[Stampy] Found {len(webhooks)} existing webhooks")
            for wh in webhooks:
                if wh.name == STAMPY_NAME:
                    print(f"[Stampy] Found existing Stampy webhook")
                    self._webhooks[channel.id] = wh
                    return wh

            print(f"[Stampy] Creating new webhook...")
            webhook = await channel.create_webhook(name=STAMPY_NAME)
            print(f"[Stampy] Created webhook: {webhook.id}")
            self._webhooks[channel.id] = webhook
            return webhook
        except Exception as e:
            print(f"[Stampy] Error getting/creating webhook: {e}")
            traceback.print_exc()
            raise

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Respond to messages in #ask-stampy channel."""
        if message.author.bot:
            return

        if message.channel.name != ASK_STAMPY_CHANNEL:
            return

        print(f"[Stampy] Received message in #ask-stampy: {message.content[:50]}...")

        try:
            await self._stream_response(message)
        except Exception as e:
            print(f"[Stampy] Error in on_message: {e}")
            traceback.print_exc()
            # Fallback to regular message if webhook fails
            try:
                await message.reply(f"Error: {e}")
            except:
                pass

    async def _stream_response(self, message: discord.Message):
        """Stream Stampy response via webhook with thinking + answer messages."""
        print(f"[Stampy] Starting stream_response")

        webhook = await self._get_webhook(message.channel)
        print(f"[Stampy] Got webhook, sending initial thinking message...")

        # Char limit for formatted content (leave room for prefix/suffix)
        THINKING_CHAR_LIMIT = 1800

        # Initial thinking message
        thinking_msg = await webhook.send(
            "*Thinking...*",
            username=STAMPY_NAME,
            avatar_url=STAMPY_AVATAR,
            wait=True,
        )
        print(f"[Stampy] Sent thinking message: {thinking_msg.id}")

        thinking_msgs = [thinking_msg]  # Track all thinking messages
        thinking_chunks = []
        thinking_finalized_chars = 0  # How many chars already in finalized messages
        answer_chunks = []
        answer_msg = None
        last_thinking_update = 0
        last_answer_len = 0

        try:
            async for state, content in stampy.ask(message.content):
                if state == "thinking":
                    thinking_chunks.append(content)
                    full_thinking = "".join(thinking_chunks)
                    current_msg_content = full_thinking[thinking_finalized_chars:]

                    # Check if we need a continuation message
                    if len(current_msg_content) > THINKING_CHAR_LIMIT:
                        # Finalize current thinking message
                        finalize_text = current_msg_content[:THINKING_CHAR_LIMIT]
                        display = format_thinking(finalize_text, "*Thinking:*")
                        await thinking_msgs[-1].edit(content=display)
                        thinking_finalized_chars += len(finalize_text)

                        # Start new continuation message
                        remaining = current_msg_content[THINKING_CHAR_LIMIT:]
                        new_msg = await webhook.send(
                            format_thinking(remaining[:THINKING_CHAR_LIMIT], "*Thinking (continued)...*"),
                            username=STAMPY_NAME,
                            avatar_url=STAMPY_AVATAR,
                            wait=True,
                        )
                        thinking_msgs.append(new_msg)
                        last_thinking_update = len(full_thinking)
                        print(f"[Stampy] Created thinking continuation message #{len(thinking_msgs)}")

                    # Update every 100 chars
                    elif len(full_thinking) - last_thinking_update > 100:
                        prefix = "*Thinking...*" if len(thinking_msgs) == 1 else "*Thinking (continued)...*"
                        display = format_thinking(current_msg_content, prefix)
                        await thinking_msgs[-1].edit(content=display)
                        last_thinking_update = len(full_thinking)

                elif state == "streaming":
                    # First streaming chunk - finalize thinking, start answer
                    if answer_msg is None:
                        # Finalize all thinking messages
                        final_thinking = "".join(thinking_chunks)
                        if final_thinking:
                            # Finalize the last thinking message
                            current_msg_content = final_thinking[thinking_finalized_chars:]
                            prefix = "*Thinking:*" if len(thinking_msgs) == 1 else "*Thinking (continued):*"
                            display = format_thinking(current_msg_content, prefix)
                            await thinking_msgs[-1].edit(content=display)
                            print(f"[Stampy] Finalized thinking: {len(final_thinking)} chars in {len(thinking_msgs)} message(s)")
                        else:
                            await thinking_msgs[-1].edit(content="*(No thinking content)*")

                        # Start answer message
                        answer_msg = await webhook.send(
                            "**Answer:**\nGenerating...",
                            username=STAMPY_NAME,
                            avatar_url=STAMPY_AVATAR,
                            wait=True,
                        )
                        print(f"[Stampy] Sent answer message: {answer_msg.id}")

                    answer_chunks.append(content)
                    current = "".join(answer_chunks)
                    # Update every 100 chars
                    if len(current) - last_answer_len > 100:
                        display = current[:1990] + "..." if len(current) > 1990 else current
                        await answer_msg.edit(content=display)
                        last_answer_len = len(current)

            # Final answer
            final_answer = "".join(answer_chunks)
            print(f"[Stampy] Got {len(final_answer)} chars of answer")

            if answer_msg:
                header = "**Answer:**\n"
                if len(header + final_answer) > 2000:
                    await answer_msg.edit(content=header + final_answer[:1990-len(header)] + "...")
                    for i in range(1990-len(header), len(final_answer), 1990):
                        await webhook.send(
                            final_answer[i:i+1990],
                            username=STAMPY_NAME,
                            avatar_url=STAMPY_AVATAR,
                        )
                else:
                    await answer_msg.edit(content=header + final_answer if final_answer else "No response received")
            else:
                # No streaming content received, just thinking
                await thinking_msgs[-1].edit(content="*(No answer received - only thinking)*")

        except Exception as e:
            print(f"[Stampy] Error streaming: {e}")
            traceback.print_exc()
            if answer_msg:
                await answer_msg.edit(content=f"Error: {str(e)}")
            else:
                await thinking_msgs[-1].edit(content=f"Error: {str(e)}")


async def setup(bot):
    await bot.add_cog(StampyCog(bot))
