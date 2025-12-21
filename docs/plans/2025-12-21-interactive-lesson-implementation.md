# Interactive Lesson Prototype Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a prototype page that alternates between AI-driven Socratic conversations and YouTube video segments.

**Architecture:** Backend uses Anthropic SDK in `core/lesson_chat.py` (platform-agnostic), exposed via FastAPI endpoint in `web_api/routes/lesson.py`. Frontend is a single React page with three states: conversation, transition prompt, and video player.

**Tech Stack:** FastAPI + Anthropic SDK (backend), React + TypeScript + react-youtube + Tailwind (frontend)

---

## Task 1: Add Anthropic SDK dependency

**Files:**
- Modify: `requirements.txt`

**Step 1: Add anthropic to requirements.txt**

Add this line after the `httpx` line:

```
anthropic>=0.40.0
```

**Step 2: Install the dependency**

Run: `pip install anthropic`

**Step 3: Commit**

```bash
jj describe -m "Add anthropic SDK dependency"
```

---

## Task 2: Create core/lesson_chat.py

**Files:**
- Create: `core/lesson_chat.py`

**Step 1: Create the lesson chat module**

```python
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
```

**Step 2: Verify the file was created correctly**

Run: `python -c "from core.lesson_chat import send_message, TRANSITION_TOOL; print('OK')"`

Expected: `OK`

**Step 3: Commit**

```bash
jj describe -m "Add core/lesson_chat.py with Claude SDK integration"
```

---

## Task 3: Export lesson_chat from core/__init__.py

**Files:**
- Modify: `core/__init__.py`

**Step 1: Add import**

After line 58 (`from core import stampy`), add:

```python
from core import lesson_chat
```

**Step 2: Add to __all__**

In the `__all__` list, after `'stampy',`, add:

```python
    'lesson_chat',
```

**Step 3: Verify**

Run: `python -c "from core import lesson_chat; print('OK')"`

Expected: `OK`

**Step 4: Commit**

```bash
jj describe -m "Export lesson_chat from core module"
```

---

## Task 4: Create web_api/routes/lesson.py

**Files:**
- Create: `web_api/routes/lesson.py`

**Step 1: Create the API route**

```python
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
```

**Step 2: Verify syntax**

Run: `python -c "from web_api.routes.lesson import router; print('OK')"`

Expected: `OK`

**Step 3: Commit**

```bash
jj describe -m "Add POST /api/chat/lesson endpoint"
```

---

## Task 5: Register lesson router in main.py

**Files:**
- Modify: `main.py`

**Step 1: Add import**

After line 50 (`from web_api.routes.users import router as users_router`), add:

```python
from web_api.routes.lesson import router as lesson_router
```

**Step 2: Include router**

After line 211 (`app.include_router(users_router)`), add:

```python
app.include_router(lesson_router)
```

**Step 3: Verify server starts**

Run: `python main.py --no-bot &` then `curl http://localhost:8000/api/status`

Expected: `{"status":"ok",...}`

Kill the server after verification.

**Step 4: Commit**

```bash
jj describe -m "Register lesson chat router in main.py"
```

---

## Task 6: Add react-youtube dependency

**Files:**
- Modify: `web_frontend/package.json`

**Step 1: Install react-youtube**

Run: `cd web_frontend && npm install react-youtube`

**Step 2: Verify it was added**

Check `package.json` contains `"react-youtube"` in dependencies.

**Step 3: Commit**

```bash
jj describe -m "Add react-youtube dependency"
```

---

## Task 7: Create lesson types

**Files:**
- Create: `web_frontend/src/types/lesson.ts`

**Step 1: Create the types file**

```typescript
/**
 * Types for interactive lesson feature.
 */

export type ConversationItem = {
  type: "conversation";
  prompt: string;
  systemContext?: string;
};

export type VideoItem = {
  type: "video";
  videoId: string;
  start: number; // seconds
  end: number; // seconds
};

export type LessonItem = ConversationItem | VideoItem;

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type LessonState =
  | { mode: "conversation"; itemIndex: number; messages: ChatMessage[]; pendingTransition: boolean }
  | { mode: "video"; itemIndex: number }
  | { mode: "complete" };
```

**Step 2: Commit**

```bash
jj describe -m "Add lesson types"
```

---

## Task 8: Create sample lesson data

**Files:**
- Create: `web_frontend/src/data/sampleLesson.ts`

**Step 1: Create the sample lesson**

```typescript
import type { LessonItem } from "../types/lesson";

/**
 * Sample lesson for testing the interactive lesson prototype.
 * Uses a real AI safety video with relevant timestamps.
 */
export const sampleLesson: LessonItem[] = [
  {
    type: "conversation",
    prompt: "Do you think AGI — artificial general intelligence — is possible?",
    systemContext:
      "This is the opening question. Get the user to commit to a position, then probe their reasoning. If they say yes, ask how they would respond to someone who says it's impossible. If they say no, ask them to explain why.",
  },
  {
    type: "video",
    // Robert Miles - "Why AI Safety?"
    videoId: "pYXy-A4siMw",
    start: 0,
    end: 120,
  },
  {
    type: "conversation",
    prompt: "What stood out to you from that segment?",
    systemContext:
      "This is a reflection question after the first video segment. Help them connect what they just watched to their earlier thinking. Ask what surprised them or challenged their assumptions.",
  },
  {
    type: "video",
    videoId: "pYXy-A4siMw",
    start: 120,
    end: 240,
  },
  {
    type: "conversation",
    prompt: "Based on what you've seen so far, what do you think are the main challenges in ensuring AI systems are safe?",
    systemContext:
      "Final reflection. Help them synthesize their learning. If their answer is shallow, probe deeper. If they mention alignment, ask them to elaborate on what that means.",
  },
];
```

**Step 2: Commit**

```bash
jj describe -m "Add sample lesson data"
```

---

## Task 9: Create VideoPlayer component

**Files:**
- Create: `web_frontend/src/components/lesson/VideoPlayer.tsx`

**Step 1: Create the component**

```typescript
import { useEffect, useRef, useCallback } from "react";
import YouTube, { YouTubePlayer, YouTubeEvent } from "react-youtube";

type VideoPlayerProps = {
  videoId: string;
  start: number;
  end: number;
  onEnded: () => void;
  onSkip: () => void;
};

export default function VideoPlayer({
  videoId,
  start,
  end,
  onEnded,
  onSkip,
}: VideoPlayerProps) {
  const playerRef = useRef<YouTubePlayer | null>(null);
  const checkIntervalRef = useRef<number | null>(null);

  const startEndCheck = useCallback(() => {
    // Clear any existing interval
    if (checkIntervalRef.current) {
      clearInterval(checkIntervalRef.current);
    }

    // Check every 500ms if we've reached the end time
    checkIntervalRef.current = window.setInterval(() => {
      if (playerRef.current) {
        const currentTime = playerRef.current.getCurrentTime();
        if (currentTime >= end) {
          playerRef.current.pauseVideo();
          if (checkIntervalRef.current) {
            clearInterval(checkIntervalRef.current);
          }
          onEnded();
        }
      }
    }, 500);
  }, [end, onEnded]);

  const handleReady = (event: YouTubeEvent) => {
    playerRef.current = event.target;
    // Seek to start and play
    event.target.seekTo(start, true);
    event.target.playVideo();
    startEndCheck();
  };

  const handleStateChange = (event: YouTubeEvent) => {
    // If user manually seeks past end or video ends naturally
    if (event.data === YouTube.PlayerState?.ENDED) {
      onEnded();
    }
    // Restart check when playing
    if (event.data === YouTube.PlayerState?.PLAYING) {
      startEndCheck();
    }
  };

  // Cleanup interval on unmount
  useEffect(() => {
    return () => {
      if (checkIntervalRef.current) {
        clearInterval(checkIntervalRef.current);
      }
    };
  }, []);

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="w-full max-w-3xl aspect-video">
        <YouTube
          videoId={videoId}
          opts={{
            width: "100%",
            height: "100%",
            playerVars: {
              start,
              autoplay: 1,
              modestbranding: 1,
              rel: 0,
            },
          }}
          onReady={handleReady}
          onStateChange={handleStateChange}
          className="w-full h-full"
          iframeClassName="w-full h-full"
        />
      </div>
      <button
        onClick={onSkip}
        className="text-gray-500 hover:text-gray-700 text-sm underline"
      >
        Skip to next question
      </button>
    </div>
  );
}
```

**Step 2: Commit**

```bash
jj describe -m "Add VideoPlayer component with timestamp control"
```

---

## Task 10: Create ConversationView component

**Files:**
- Create: `web_frontend/src/components/lesson/ConversationView.tsx`

**Step 1: Create the component**

```typescript
import { useState, useRef, useEffect } from "react";
import type { ChatMessage } from "../../types/lesson";

type ConversationViewProps = {
  messages: ChatMessage[];
  onSendMessage: (content: string) => void;
  onSkipToVideo: () => void;
  isLoading: boolean;
  pendingTransition: boolean;
  onConfirmTransition: () => void;
  onContinueChatting: () => void;
};

export default function ConversationView({
  messages,
  onSendMessage,
  onSkipToVideo,
  isLoading,
  pendingTransition,
  onConfirmTransition,
  onContinueChatting,
}: ConversationViewProps) {
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim());
      setInput("");
    }
  };

  return (
    <div className="flex flex-col h-full max-w-2xl mx-auto">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`p-3 rounded-lg ${
              msg.role === "assistant"
                ? "bg-blue-50 text-gray-800"
                : "bg-gray-100 text-gray-800 ml-8"
            }`}
          >
            <div className="text-xs text-gray-500 mb-1">
              {msg.role === "assistant" ? "Claude" : "You"}
            </div>
            <div className="whitespace-pre-wrap">{msg.content}</div>
          </div>
        ))}
        {isLoading && (
          <div className="bg-blue-50 p-3 rounded-lg">
            <div className="text-xs text-gray-500 mb-1">Claude</div>
            <div className="text-gray-500">Thinking...</div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Transition prompt */}
      {pendingTransition && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
          <p className="text-gray-700 mb-3">
            Ready to watch the next video segment?
          </p>
          <div className="flex gap-2">
            <button
              onClick={onConfirmTransition}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            >
              Watch video
            </button>
            <button
              onClick={onContinueChatting}
              className="bg-gray-200 text-gray-700 px-4 py-2 rounded hover:bg-gray-300"
            >
              Continue chatting
            </button>
          </div>
        </div>
      )}

      {/* Input form */}
      {!pendingTransition && (
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your response..."
            disabled={isLoading}
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </form>
      )}

      {/* Skip button */}
      {!pendingTransition && (
        <button
          onClick={onSkipToVideo}
          className="mt-2 text-gray-500 hover:text-gray-700 text-sm underline self-end"
        >
          Skip to video
        </button>
      )}
    </div>
  );
}
```

**Step 2: Commit**

```bash
jj describe -m "Add ConversationView component"
```

---

## Task 11: Create InteractiveLessonPage

**Files:**
- Create: `web_frontend/src/pages/InteractiveLesson.tsx`

**Step 1: Create the page component**

```typescript
import { useState, useCallback } from "react";
import type { ChatMessage, LessonState, LessonItem } from "../types/lesson";
import { sampleLesson } from "../data/sampleLesson";
import ConversationView from "../components/lesson/ConversationView";
import VideoPlayer from "../components/lesson/VideoPlayer";

export default function InteractiveLesson() {
  const [lessonState, setLessonState] = useState<LessonState>(() => {
    const firstItem = sampleLesson[0];
    if (firstItem.type === "conversation") {
      return {
        mode: "conversation",
        itemIndex: 0,
        messages: [{ role: "assistant", content: firstItem.prompt }],
        pendingTransition: false,
      };
    }
    return { mode: "video", itemIndex: 0 };
  });

  const [isLoading, setIsLoading] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");

  const currentItem: LessonItem | undefined = sampleLesson[
    lessonState.mode === "complete" ? -1 : lessonState.itemIndex
  ];

  const moveToNextItem = useCallback(() => {
    const nextIndex =
      lessonState.mode === "complete" ? 0 : lessonState.itemIndex + 1;
    if (nextIndex >= sampleLesson.length) {
      setLessonState({ mode: "complete" });
      return;
    }

    const nextItem = sampleLesson[nextIndex];
    if (nextItem.type === "conversation") {
      setLessonState({
        mode: "conversation",
        itemIndex: nextIndex,
        messages: [{ role: "assistant", content: nextItem.prompt }],
        pendingTransition: false,
      });
    } else {
      setLessonState({ mode: "video", itemIndex: nextIndex });
    }
  }, [lessonState]);

  const sendMessage = useCallback(
    async (content: string) => {
      if (lessonState.mode !== "conversation") return;

      const userMessage: ChatMessage = { role: "user", content };
      const updatedMessages = [...lessonState.messages, userMessage];

      setLessonState({
        ...lessonState,
        messages: updatedMessages,
        pendingTransition: false,
      });
      setIsLoading(true);
      setStreamingContent("");

      try {
        const currentConvItem = currentItem as { type: "conversation"; prompt: string; systemContext?: string };

        const response = await fetch("/api/chat/lesson", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            messages: updatedMessages,
            system_context: currentConvItem.systemContext,
          }),
        });

        if (!response.ok) throw new Error("Failed to send message");

        const reader = response.body?.getReader();
        if (!reader) throw new Error("No response body");

        const decoder = new TextDecoder();
        let assistantContent = "";
        let shouldTransition = false;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split("\n");

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === "text") {
                assistantContent += data.content;
                setStreamingContent(assistantContent);
              } else if (data.type === "tool_use" && data.name === "transition_to_video") {
                shouldTransition = true;
              }
            } catch {
              // Skip invalid JSON
            }
          }
        }

        // Add assistant message
        const assistantMessage: ChatMessage = {
          role: "assistant",
          content: assistantContent,
        };

        setLessonState({
          mode: "conversation",
          itemIndex: lessonState.itemIndex,
          messages: [...updatedMessages, assistantMessage],
          pendingTransition: shouldTransition,
        });
      } catch (error) {
        console.error("Error sending message:", error);
        // Add error message
        setLessonState({
          ...lessonState,
          messages: [
            ...updatedMessages,
            { role: "assistant", content: "Sorry, something went wrong. Please try again." },
          ],
          pendingTransition: false,
        });
      } finally {
        setIsLoading(false);
        setStreamingContent("");
      }
    },
    [lessonState, currentItem]
  );

  const handleSkipToVideo = useCallback(() => {
    moveToNextItem();
  }, [moveToNextItem]);

  const handleConfirmTransition = useCallback(() => {
    moveToNextItem();
  }, [moveToNextItem]);

  const handleContinueChatting = useCallback(() => {
    if (lessonState.mode === "conversation") {
      setLessonState({ ...lessonState, pendingTransition: false });
    }
  }, [lessonState]);

  const handleVideoEnded = useCallback(() => {
    moveToNextItem();
  }, [moveToNextItem]);

  const handleVideoSkip = useCallback(() => {
    moveToNextItem();
  }, [moveToNextItem]);

  const handleRestart = useCallback(() => {
    const firstItem = sampleLesson[0];
    if (firstItem.type === "conversation") {
      setLessonState({
        mode: "conversation",
        itemIndex: 0,
        messages: [{ role: "assistant", content: firstItem.prompt }],
        pendingTransition: false,
      });
    } else {
      setLessonState({ mode: "video", itemIndex: 0 });
    }
  }, []);

  // Calculate progress
  const progress =
    lessonState.mode === "complete"
      ? 100
      : Math.round((lessonState.itemIndex / sampleLesson.length) * 100);

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Interactive Lesson Prototype
          </h1>
          <div className="flex items-center gap-4">
            <div className="flex-1 bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
            <span className="text-sm text-gray-500">{progress}%</span>
          </div>
        </div>

        {/* Main content */}
        <div className="bg-white rounded-lg shadow-sm p-6 min-h-[500px]">
          {lessonState.mode === "conversation" && (
            <ConversationView
              messages={
                isLoading && streamingContent
                  ? [
                      ...lessonState.messages,
                      { role: "assistant", content: streamingContent },
                    ]
                  : lessonState.messages
              }
              onSendMessage={sendMessage}
              onSkipToVideo={handleSkipToVideo}
              isLoading={isLoading}
              pendingTransition={lessonState.pendingTransition}
              onConfirmTransition={handleConfirmTransition}
              onContinueChatting={handleContinueChatting}
            />
          )}

          {lessonState.mode === "video" && currentItem?.type === "video" && (
            <VideoPlayer
              videoId={currentItem.videoId}
              start={currentItem.start}
              end={currentItem.end}
              onEnded={handleVideoEnded}
              onSkip={handleVideoSkip}
            />
          )}

          {lessonState.mode === "complete" && (
            <div className="text-center py-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Lesson Complete!
              </h2>
              <p className="text-gray-600 mb-6">
                Great work exploring these ideas about AI safety.
              </p>
              <button
                onClick={handleRestart}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
              >
                Start Over
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
```

**Step 2: Commit**

```bash
jj describe -m "Add InteractiveLessonPage component"
```

---

## Task 12: Add route to App.tsx

**Files:**
- Modify: `web_frontend/src/App.tsx`

**Step 1: Add import**

After line 5 (`import NotFound from "./pages/NotFound";`), add:

```typescript
import InteractiveLesson from "./pages/InteractiveLesson";
```

**Step 2: Add route**

After line 14 (`<Route path="/auth/code" element={<Auth />} />`), add:

```typescript
        <Route path="/prototype/interactive-lesson" element={<InteractiveLesson />} />
```

**Step 3: Verify**

Run: `cd web_frontend && npm run build`

Expected: Build succeeds without errors.

**Step 4: Commit**

```bash
jj describe -m "Add /prototype/interactive-lesson route"
```

---

## Task 13: Add ANTHROPIC_API_KEY to environment

**Files:**
- Modify: `.env.local` (or `.env`)

**Step 1: Add the API key**

Add this line:

```
ANTHROPIC_API_KEY=your_api_key_here
```

Replace with your actual Anthropic API key.

**Step 2: Verify**

Run: `python -c "import os; from dotenv import load_dotenv; load_dotenv('.env.local'); print('Key present:', bool(os.environ.get('ANTHROPIC_API_KEY')))"`

Expected: `Key present: True`

**Note:** Do NOT commit `.env.local` — it should already be in `.gitignore`.

---

## Task 14: End-to-end test

**Step 1: Start the dev server**

Run: `python main.py --dev --no-bot`

**Step 2: Open the prototype**

Navigate to: `http://localhost:5173/prototype/interactive-lesson`

**Step 3: Test the flow**

1. Page should show Claude's opening question
2. Type a response and send
3. Claude should respond (streamed)
4. After a few exchanges, Claude should trigger the transition prompt
5. Click "Watch video" — YouTube should play
6. When video segment ends (or click skip), next conversation starts
7. Complete all segments to see completion screen

**Step 4: Final commit**

```bash
jj describe -m "Interactive lesson prototype complete"
```

---

## Summary

**Files created:**
- `core/lesson_chat.py` — Claude SDK integration
- `web_api/routes/lesson.py` — API endpoint
- `web_frontend/src/types/lesson.ts` — TypeScript types
- `web_frontend/src/data/sampleLesson.ts` — Sample lesson data
- `web_frontend/src/components/lesson/VideoPlayer.tsx` — YouTube player
- `web_frontend/src/components/lesson/ConversationView.tsx` — Chat UI
- `web_frontend/src/pages/InteractiveLesson.tsx` — Main page

**Files modified:**
- `requirements.txt` — Added anthropic SDK
- `core/__init__.py` — Export lesson_chat
- `main.py` — Register lesson router
- `web_frontend/package.json` — Added react-youtube
- `web_frontend/src/App.tsx` — Added route
