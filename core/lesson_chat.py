"""
Lesson chat - Claude SDK integration for interactive lessons.

Platform-agnostic: can be used by web API or any other interface.
"""

import os
from typing import AsyncIterator

from anthropic import AsyncAnthropic


# Tool definition for transitioning to video
TRANSITION_TOOL = {
    "name": "transition_to_video",
    "description": (
        "Call this when the conversation has reached a good stopping point "
        "and the user is ready to watch the next video segment. "
        "Use this after 2-4 exchanges, or when the user seems ready to move on."
    ),
    "input_schema": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}

# Base system prompt for lesson conversations
BASE_SYSTEM_PROMPT = """You are a Socratic tutor helping someone learn about AI safety.

Your role:
- Ask probing questions to help them think deeply
- Challenge their assumptions constructively
- If they hold a correct view, present counterarguments to strengthen their understanding
- If they hold an incorrect view, ask them to explain their reasoning to surface misconceptions
- Keep responses concise (2-3 sentences typically)
- After 2-4 meaningful exchanges, use the transition_to_video tool to move to the next video segment

Do NOT:
- Give long lectures
- Simply agree with everything they say
- Be dismissive or condescending
"""


async def send_message(
    messages: list[dict],
    system_context: str | None = None,
) -> AsyncIterator[dict]:
    """
    Send messages to Claude and stream the response.

    Args:
        messages: List of {"role": "user"|"assistant", "content": str}
        system_context: Optional additional context to append to system prompt

    Yields:
        Dicts with either:
        - {"type": "text", "content": str} for text chunks
        - {"type": "tool_use", "name": str} for tool calls
        - {"type": "done"} when complete
    """
    client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    # Build system prompt
    system = BASE_SYSTEM_PROMPT
    if system_context:
        system += f"\n\nAdditional context for this conversation:\n{system_context}"

    # Stream response
    async with client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=system,
        messages=messages,
        tools=[TRANSITION_TOOL],
    ) as stream:
        async for event in stream:
            if event.type == "content_block_start":
                if event.content_block.type == "tool_use":
                    yield {"type": "tool_use", "name": event.content_block.name}
            elif event.type == "content_block_delta":
                if event.delta.type == "text_delta":
                    yield {"type": "text", "content": event.delta.text}

        yield {"type": "done"}
