"""
Lesson chat API routes.

Endpoints:
- POST /api/chat/lesson - Send message and stream response
"""

import json
import sys
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.lessons.chat import send_message
from core.lessons.types import ChatStage
from web_api.auth import get_current_user

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
    # Create a ChatStage with the system_context as instructions
    stage = ChatStage(
        type="chat",
        instructions=system_context or "Help the user learn about AI safety.",
    )
    try:
        async for chunk in send_message(messages, stage, None, None):
            yield f"data: {json.dumps(chunk)}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"


@router.post("/lesson")
async def chat_lesson(
    request: LessonChatRequest,
    user: dict = Depends(get_current_user),
) -> StreamingResponse:
    """
    Send a message to the lesson chat and stream the response.

    Requires authentication to prevent API cost abuse.

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
