"""
Lesson chat API routes.

Endpoints:
- POST /api/chat/lesson - Send message and stream response
"""

import json
import sys
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core import lesson_chat

router = APIRouter(prefix="/api/chat", tags=["lesson"])


class ChatMessage(BaseModel):
    """A single chat message."""

    role: str  # "user" or "assistant"
    content: str


class LessonChatRequest(BaseModel):
    """Request body for lesson chat."""

    messages: list[ChatMessage]
    system_context: str | None = None


async def event_generator(messages: list[dict], system_context: str | None):
    """Generate SSE events from Claude stream."""
    try:
        async for chunk in lesson_chat.send_message(messages, system_context):
            yield f"data: {json.dumps(chunk)}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"


@router.post("/lesson")
async def chat_lesson(request: LessonChatRequest) -> StreamingResponse:
    """
    Send a message to the lesson chat and stream the response.

    Returns Server-Sent Events with:
    - {"type": "text", "content": "..."} for text chunks
    - {"type": "tool_use", "name": "transition_to_video"} when Claude wants to transition
    - {"type": "done"} when complete
    - {"type": "error", "message": "..."} on error
    """
    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    return StreamingResponse(
        event_generator(messages, request.system_context),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
