"""
Stampy chatbot integration.
"""
import json
import os
import httpx
from typing import AsyncIterator


STAMPY_API_URL = os.getenv("STAMPY_API_URL", "https://chat.stampy.ai:8443/chat")


async def ask(query: str) -> AsyncIterator[tuple[str, str]]:
    """
    Send query to Stampy and stream response.

    Yields (state, content) tuples where state is "thinking" or "streaming".
    No history - each question is independent.
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream(
            "POST",
            STAMPY_API_URL,
            json={
                "query": query,
                "sessionId": "discord-ask-stampy",
                "stream": True,
            },
        ) as response:
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue

                try:
                    data = json.loads(line[6:])
                except json.JSONDecodeError:
                    continue

                state = data.get("state")
                if state in ("thinking", "streaming"):
                    content = data.get("content", "")
                    if content:
                        yield (state, content)
