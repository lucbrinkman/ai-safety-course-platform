# Interactive Lesson Prototype Design

## Overview

A prototype feature for interactive learning that alternates between AI-driven Socratic conversations and YouTube video segments. The goal is to increase engagement and retention by creating "cognitive gaps" — prompting learners to commit to a position, challenging them, and then delivering content that resolves the tension.

**Route:** `/prototype/interactive-lesson`

## Pedagogical Approach

The pattern:
1. **Position elicitation** — Ask the learner what they think
2. **Challenge or probe** — If correct view, challenge with counterarguments. If incorrect, ask them to explain their reasoning
3. **Content delivery** — Video segment that addresses what was surfaced
4. **Active recall** — Follow-up questions to check retention

For MVP: Linear flow only, no branching based on responses. Just alternating conversation → video → conversation → video.

## Core Flow

```
[Claude opens with question]
        ↓
[Back-and-forth chat]
        ↓
[Claude calls transition tool OR user clicks "Skip"]
        ↓
[User confirms → Video plays segment]
        ↓
[Video ends → Next conversation begins]
        ↓
[Repeat until lesson complete]
```

## Lesson Data Structure

Hardcoded in frontend code, JSON-shaped for future extraction:

```typescript
type LessonItem =
  | { type: 'conversation'; prompt: string; systemContext?: string }
  | { type: 'video'; videoId: string; start: number; end: number };

const lessonFlow: LessonItem[] = [
  {
    type: 'conversation',
    prompt: 'Do you think AGI is possible?',
    systemContext: 'Challenge the user to defend their position...'
  },
  {
    type: 'video',
    videoId: 'abc123',  // YouTube video ID
    start: 0,
    end: 150  // seconds
  },
  {
    type: 'conversation',
    prompt: 'What stood out to you from that segment?'
  },
  {
    type: 'video',
    videoId: 'abc123',
    start: 150,
    end: 320
  },
];
```

**Notes:**
- `prompt` — What Claude opens with
- `systemContext` — Optional per-conversation guidance for Claude
- `videoId` — YouTube ID (the part after `v=`)
- `start`/`end` — Timestamps in seconds

**Future extensions:**
- Add `{ type: 'multipleChoice', question: '...', options: [...] }`
- Move to database/API when ready

## UI Design

Single-focus layout — one main area showing one of three states:

### State 1: Conversation
```
┌───────────────────────────────┐
│ Claude: Do you think AGI is   │
│ possible?                     │
├───────────────────────────────┤
│ You: Yes, because...          │
├───────────────────────────────┤
│ Claude: But what about...     │
└───────────────────────────────┘
┌───────────────────────────────┐
│ [Type your response...]       │
└───────────────────────────────┘
                  [Skip to video]
```

### State 2: Transition Prompt
```
Claude suggests watching the next segment.

[Continue chatting] [Watch video]
```

### State 3: Video Player
```
┌───────────────────────────────┐
│                               │
│       YouTube Embed           │
│       (auto-plays segment)    │
│                               │
└───────────────────────────────┘
           [Skip to question]
```

## Components

- `InteractiveLessonPage` — Page wrapper, manages current lesson state
- `ConversationView` — Chat UI with message history + input
- `TransitionPrompt` — Confirmation when Claude suggests moving on
- `VideoPlayer` — YouTube embed with timestamp control (using `react-youtube`)
- `LessonProgress` — Optional: indicator showing position in lesson

## Backend Architecture

Follows 3-layer architecture with logic in `core/`:

```
core/
  └── lesson_chat.py       # Claude SDK integration (platform-agnostic)
                           # - send_lesson_message(messages, system_context)
                           # - defines tools, handles streaming
                           # - returns response + tool calls

web_api/
  └── routes/
        └── lesson.py      # Thin HTTP adapter
                           # - POST /api/chat/lesson
                           # - imports from core/lesson_chat
                           # - handles request/response serialization
```

### API Endpoint

```
POST /api/chat/lesson
```

**Request:**
```json
{
  "messages": [
    { "role": "assistant", "content": "Do you think AGI is possible?" },
    { "role": "user", "content": "Yes, because..." }
  ],
  "systemContext": "Challenge the user to defend their position..."
}
```

**Response (streamed):**
```json
{
  "content": "That's interesting, but what about...",
  "toolCall": null
}
```

Or when Claude wants to transition:
```json
{
  "content": "Good discussion! I think you're ready to see...",
  "toolCall": { "name": "transition_to_video" }
}
```

### Tool Definition

```python
tools = [{
    "name": "transition_to_video",
    "description": "Call this when the conversation has reached a good stopping point and the user is ready to watch the next video segment."
}]
```

## Tech Stack

**Frontend:**
- React + TypeScript (existing)
- `react-youtube` for YouTube embeds
- Streaming chat via `fetch` with ReadableStream

**Backend:**
- `core/lesson_chat.py` — Anthropic SDK
- `web_api/routes/lesson.py` — FastAPI endpoint
- Streaming via `StreamingResponse`

**New dependencies:**
- Backend: `anthropic` Python SDK
- Frontend: `react-youtube`

**Environment:**
- New env var: `ANTHROPIC_API_KEY`

## MVP Scope

**Included:**
- Single prototype page at `/prototype/interactive-lesson`
- Linear lesson flow (no branching)
- Free-text responses only
- Claude-powered Socratic conversation
- YouTube video segments with start/end timestamps
- LLM-suggested transitions with user confirmation
- User can skip at any time

**Not included:**
- Authentication
- Persistence (ephemeral — refresh = start over)
- Branching logic based on responses
- Multiple choice questions
- Progress saving
- Course integration
- Mobile optimization
