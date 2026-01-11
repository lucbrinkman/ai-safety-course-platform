# Course Overview Page Design

## Overview

A course overview page optimized for enrolled learners (80%) to resume where they left off and see the full course picture. External visitors are a secondary concern for now.

## Layout

Two-panel layout at `/course/:courseId`:

```
┌─────────────────────────────────────────────────────────────────┐
│  Breadcrumb: AI Safety Fundamentals > Module Name > Lesson Name │
├────────────────────┬────────────────────────────────────────────┤
│                    │                                            │
│  Module Sidebar    │  Main Panel (LessonOverview)               │
│  (~280px)          │                                            │
│                    │  Lesson Title                              │
│  ▼ Foundations     │  Description                               │
│    ✓ Intro         │                                            │
│    ● Current  ←    │  [✓]─── 📄 Article Title                   │
│      Future        │         Article · 5 min read               │
│                    │                                            │
│  ▶ Module 2        │  [✓]─── ▶️ Video Title                     │
│  ▶ Module 3        │         Video · 8 min                      │
│                    │                                            │
│                    │  [ ]─── 💬 Reflection                      │
│                    │    ●    Discuss with AI tutor              │
│                    │    │                                       │
│                    │                                            │
│                    │  [ Continue Lesson ]                       │
│                    │                                            │
└────────────────────┴────────────────────────────────────────────┘
```

## Components

### ModuleSidebar

Accordion list of modules, each expandable to show lessons.

**Module item:**
- Module title + expand/collapse chevron
- Optional progress indicator (e.g., "3/5")

**Lesson item states:**
- Completed: checkmark + normal text
- Current: filled dot + highlighted background
- Future: hollow dot + normal text

**Behavior:**
- On page load, auto-expand module containing user's current lesson
- Auto-select current lesson so main panel shows it immediately
- Clicking a lesson selects it (updates main panel)

### LessonOverview

Vertical stage list with progress line. Reused in two contexts:
1. Course overview main panel
2. In-player slide-out drawer

**Stage row contents:**
- Icon (article/video/chat)
- Title
- Brief descriptor: type + time estimate
- Chat stages: generic "Discuss with AI tutor"

**Progress indicators:**
- Vertical line on left, filled up to current stage
- Checkmarks on completed stages
- Current stage: filled dot or pulsing indicator
- Future stages: hollow/muted

**Actions at bottom:**
- "Start Lesson" (not started)
- "Continue Lesson" (in progress)
- "Review Lesson" (completed)

### Content Preview (Course Overview Only)

Clicking a stage in the course overview opens a standalone preview using the existing ContentPanel component in a modal. This lets users reference material they've seen or peek ahead without entering the lesson flow.

Chat stages are not previewable (they require lesson context).

## In-Player Drawer

From within the interactive lesson player, users can open a slide-out drawer showing the LessonOverview.

**Appearance:**
- Slides in from right edge
- ~40% viewport width
- Floats on top of chat panel (doesn't replace it)
- Small tab/button on right edge when collapsed

**Behavior:**
- Click tab: drawer slides in
- Click stage: navigates content panel to that stage (same as horizontal bar)
- Click close/outside: drawer slides out
- No separate preview mode - just navigation

**Visual consistency:**
The drawer uses the same LessonOverview component as the course overview, providing a familiar vertical view of the horizontal progress bar.

## Routes

| Route | Component | Description |
|-------|-----------|-------------|
| `/course/:courseId` | CourseOverviewPage | Two-panel layout with sidebar + main |
| `/course/:courseId/lesson/:lessonId` | UnifiedLesson (enhanced) | Existing player + new drawer |

## Data Requirements

**From backend:**
- Course structure: modules → lessons → stages
- User progress: completed lessons, current lesson, current stage

**New endpoint:**
```
GET /api/courses/:courseId/progress

Response:
{
  course: { id, title, description },
  modules: [
    {
      id, title,
      lessons: [
        {
          id, title, description,
          stages: [{ type, title, duration }],
          status: "completed" | "in_progress" | "not_started",
          currentStageIndex: number | null
        }
      ]
    }
  ]
}
```

**Existing support:**
- `lesson_sessions` table: `current_stage_index`, `completed_at`
- Course/lesson YAML files: structure definition

## New Components Summary

| Component | Location | Purpose |
|-----------|----------|---------|
| CourseOverviewPage | `web_frontend/src/pages/` | Two-panel layout |
| ModuleSidebar | `web_frontend/src/components/` | Accordion module/lesson list |
| LessonOverview | `web_frontend/src/components/` | Vertical stage list (shared) |
| LessonDrawer | `web_frontend/src/components/` | Slide-out wrapper for player |

## Open Questions

- Exact styling/colors for progress states
- Animation timing for drawer slide
- Mobile responsive behavior (sidebar becomes hamburger menu?)
