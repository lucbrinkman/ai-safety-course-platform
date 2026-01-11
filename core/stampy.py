"""
Stampy chatbot integration.
"""
import json
import os
import httpx
from typing import AsyncIterator, Any


STAMPY_API_URL = os.getenv("STAMPY_API_URL", "https://chat.stampy.ai:8443/chat")


async def ask(query: str) -> AsyncIterator[tuple[str, Any]]:
    """
    Send query to Stampy and stream response.

    Yields (state, content) tuples where:
    - state="thinking": content is thinking text
    - state="streaming": content is answer text
    - state="citations": content is list of citation dicts
    - state="error": content is error message
    No history - each question is independent.
    """
    try:
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
                response.raise_for_status()
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
                    elif state == "citations":
                        # Citations come as a list of objects with url, title, etc.
                        citations = data.get("citations", [])
                        if citations:
                            yield ("citations", citations)
    except httpx.HTTPStatusError as e:
        yield ("error", f"Stampy API error: {e.response.status_code}")
    except httpx.TimeoutException:
        yield ("error", "Stampy API request timed out")
    except httpx.RequestError as e:
        yield ("error", f"Network error: {e}")
