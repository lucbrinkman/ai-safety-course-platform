# Course Overview Page Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a course overview page where enrolled learners can see their progress and resume lessons, plus an in-player drawer for quick navigation.

**Architecture:** Two-panel layout (sidebar + main) at `/course/:courseId`. Sidebar shows accordion of modules/lessons. Main panel shows selected lesson's stages with progress. Same LessonOverview component reused in a slide-out drawer within the lesson player.

**Tech Stack:** React 19, TypeScript, Tailwind CSS, FastAPI, SQLAlchemy

---

## Task 1: Backend - Course Progress Endpoint

Create an endpoint that returns course structure merged with user progress.

**Files:**
- Modify: `core/lessons/sessions.py` (add function)
- Modify: `core/lessons/__init__.py` (export)
- Modify: `web_api/routes/courses.py` (add endpoint)

**Step 1: Add get_user_lesson_progress function to sessions.py**

Add this function at the end of `core/lessons/sessions.py`:

```python
async def get_user_lesson_progress(user_id: int | None) -> dict[str, dict]:
    """
    Get progress for all lessons a user has started.

    Args:
        user_id: The user's database ID (None for anonymous)

    Returns:
        Dict mapping lesson_id to progress info:
        {
            "lesson-id": {
                "status": "completed" | "in_progress" | "not_started",
                "current_stage_index": int | None,
                "session_id": int | None,
            }
        }
    """
    if user_id is None:
        return {}

    async with get_connection() as conn:
        result = await conn.execute(
            select(lesson_sessions)
            .where(lesson_sessions.c.user_id == user_id)
            .order_by(lesson_sessions.c.last_active_at.desc())
        )
        rows = result.mappings().all()

    progress = {}
    for row in rows:
        lesson_id = row["lesson_id"]
        # Only keep the most recent session per lesson
        if lesson_id not in progress:
            if row["completed_at"] is not None:
                status = "completed"
            else:
                status = "in_progress"
            progress[lesson_id] = {
                "status": status,
                "current_stage_index": row["current_stage_index"],
                "session_id": row["session_id"],
            }
    return progress
```

**Step 2: Export from __init__.py**

Add to the exports in `core/lessons/__init__.py`:

```python
from .sessions import (
    # ... existing exports ...
    get_user_lesson_progress,
)
```

Find the line with `from .sessions import` and add `get_user_lesson_progress` to the import list.

**Step 3: Add course progress endpoint**

Add to `web_api/routes/courses.py`:

```python
from fastapi import APIRouter, HTTPException, Query, Request

from core.lessons.course_loader import (
    load_course,
    get_next_lesson,
    CourseNotFoundError,
)
from core.lessons import (
    load_lesson,
    get_user_lesson_progress,
    get_stage_title,
    LessonNotFoundError,
)
from web_api.auth import get_optional_user
from core import get_or_create_user

# ... existing router definition ...

def get_stage_duration_estimate(stage) -> str | None:
    """Estimate duration for a stage."""
    if stage.type == "article":
        return "5 min read"
    elif stage.type == "video":
        if stage.to_seconds and stage.from_seconds:
            minutes = (stage.to_seconds - stage.from_seconds) // 60
            return f"{max(1, minutes)} min"
        return "Video"
    elif stage.type == "chat":
        return None
    return None


@router.get("/{course_id}/progress")
async def get_course_progress(course_id: str, request: Request):
    """Get course structure with user progress.

    Returns course modules, lessons, and stages with completion status.
    """
    # Get user if authenticated
    user_jwt = await get_optional_user(request)
    user_id = None
    if user_jwt:
        discord_id = user_jwt["sub"]
        user = await get_or_create_user(discord_id)
        user_id = user["user_id"]

    # Load course structure
    try:
        course = load_course(course_id)
    except CourseNotFoundError:
        raise HTTPException(status_code=404, detail=f"Course not found: {course_id}")

    # Get user's progress
    progress = await get_user_lesson_progress(user_id)

    # Build response with progress merged
    modules = []
    for module in course.modules:
        lessons = []
        for lesson_id in module.lessons:
            try:
                lesson = load_lesson(lesson_id)
            except LessonNotFoundError:
                continue

            lesson_progress = progress.get(lesson_id, {
                "status": "not_started",
                "current_stage_index": None,
                "session_id": None,
            })

            # Build stages info
            stages = []
            for stage in lesson.stages:
                stages.append({
                    "type": stage.type,
                    "title": get_stage_title(stage),
                    "duration": get_stage_duration_estimate(stage),
                    "optional": getattr(stage, "optional", False),
                })

            lessons.append({
                "id": lesson.id,
                "title": lesson.title,
                "stages": stages,
                "status": lesson_progress["status"],
                "currentStageIndex": lesson_progress["current_stage_index"],
                "sessionId": lesson_progress["session_id"],
            })

        modules.append({
            "id": module.id,
            "title": module.title,
            "lessons": lessons,
        })

    return {
        "course": {
            "id": course.id,
            "title": course.title,
        },
        "modules": modules,
    }
```

**Step 4: Update imports at top of courses.py**

Replace the imports at the top of the file to include Request and new imports.

**Step 5: Test manually**

```bash
# Start the server
python main.py --dev --no-bot

# Test endpoint (in another terminal)
curl http://localhost:8000/api/courses/default/progress | jq
```

Expected: JSON with course structure, modules, lessons, and stages.

**Step 6: Commit**

```bash
jj describe -m "feat: add course progress endpoint"
```

---

## Task 2: Frontend - Types and API Client

Add TypeScript types and API client function for course progress.

**Files:**
- Create: `web_frontend/src/types/course.ts`
- Modify: `web_frontend/src/api/lessons.ts` (add function)

**Step 1: Create course types**

Create `web_frontend/src/types/course.ts`:

```typescript
/**
 * Types for course overview feature.
 */

export type StageInfo = {
  type: "article" | "video" | "chat";
  title: string;
  duration: string | null;
  optional: boolean;
};

export type LessonStatus = "completed" | "in_progress" | "not_started";

export type LessonInfo = {
  id: string;
  title: string;
  stages: StageInfo[];
  status: LessonStatus;
  currentStageIndex: number | null;
  sessionId: number | null;
};

export type ModuleInfo = {
  id: string;
  title: string;
  lessons: LessonInfo[];
};

export type CourseProgress = {
  course: {
    id: string;
    title: string;
  };
  modules: ModuleInfo[];
};
```

**Step 2: Add API function to lessons.ts**

Add at the end of `web_frontend/src/api/lessons.ts`:

```typescript
import type { CourseProgress } from "../types/course";

export async function getCourseProgress(courseId: string): Promise<CourseProgress> {
  const res = await fetch(`${API_BASE}/api/courses/${courseId}/progress`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to fetch course progress");
  return res.json();
}
```

**Step 3: Commit**

```bash
jj describe -m "feat: add course progress types and API client"
```

---

## Task 3: Frontend - LessonOverview Component

Create the reusable vertical stage list component.

**Files:**
- Create: `web_frontend/src/components/course/LessonOverview.tsx`

**Step 1: Create the component**

Create directory and file `web_frontend/src/components/course/LessonOverview.tsx`:

```typescript
/**
 * Vertical stage list with progress line.
 * Reused in course overview main panel and in-player drawer.
 */

import type { StageInfo, LessonStatus } from "../../types/course";
import { StageIcon } from "../unified-lesson/StageProgressBar";

type LessonOverviewProps = {
  lessonTitle: string;
  stages: StageInfo[];
  status: LessonStatus;
  currentStageIndex: number | null;
  onStageClick?: (index: number) => void;
  onStartLesson?: () => void;
  showActions?: boolean;
};

export default function LessonOverview({
  lessonTitle,
  stages,
  status,
  currentStageIndex,
  onStageClick,
  onStartLesson,
  showActions = true,
}: LessonOverviewProps) {
  const effectiveCurrentIndex = currentStageIndex ?? -1;

  const getStageState = (index: number) => {
    if (status === "completed") return "completed";
    if (index < effectiveCurrentIndex) return "completed";
    if (index === effectiveCurrentIndex) return "current";
    return "future";
  };

  const getActionLabel = () => {
    if (status === "completed") return "Review Lesson";
    if (status === "in_progress") return "Continue Lesson";
    return "Start Lesson";
  };

  return (
    <div className="flex flex-col h-full">
      {/* Lesson title */}
      <h2 className="text-2xl font-bold text-slate-900 mb-6">{lessonTitle}</h2>

      {/* Stage list */}
      <div className="flex-1 overflow-y-auto">
        <div className="relative">
          {/* Progress line */}
          <div className="absolute left-4 top-4 bottom-4 w-0.5 bg-slate-200" />
          {status !== "not_started" && (
            <div
              className="absolute left-4 top-4 w-0.5 bg-blue-500 transition-all duration-300"
              style={{
                height: status === "completed"
                  ? "calc(100% - 2rem)"
                  : `calc(${((effectiveCurrentIndex + 0.5) / stages.length) * 100}% - 1rem)`,
              }}
            />
          )}

          {/* Stages */}
          <div className="space-y-4">
            {stages.map((stage, index) => {
              const state = getStageState(index);
              const isClickable = onStageClick && stage.type !== "chat";

              return (
                <div
                  key={index}
                  className={`relative flex items-start gap-4 pl-2 ${
                    isClickable ? "cursor-pointer hover:bg-slate-50 rounded-lg p-2 -ml-2" : "p-2 -ml-2"
                  }`}
                  onClick={() => isClickable && onStageClick(index)}
                >
                  {/* Progress dot */}
                  <div
                    className={`relative z-10 w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 ${
                      state === "completed"
                        ? "bg-blue-500 text-white"
                        : state === "current"
                        ? "bg-blue-500 text-white ring-4 ring-blue-100"
                        : "bg-slate-200 text-slate-400"
                    }`}
                  >
                    {state === "completed" ? (
                      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    ) : (
                      <div className="w-2 h-2 rounded-full bg-current" />
                    )}
                  </div>

                  {/* Stage info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <StageIcon type={stage.type} small />
                      <span
                        className={`font-medium ${
                          state === "future" ? "text-slate-400" : "text-slate-900"
                        }`}
                      >
                        {stage.title}
                      </span>
                      {stage.optional && (
                        <span className="text-xs text-slate-400 border border-slate-200 rounded px-1">
                          Optional
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-slate-500 mt-0.5">
                      {stage.type === "chat"
                        ? "Discuss with AI tutor"
                        : stage.duration || (stage.type === "article" ? "Article" : "Video")}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Action button */}
      {showActions && onStartLesson && (
        <div className="pt-6 mt-auto border-t border-slate-100">
          <button
            onClick={onStartLesson}
            className="w-full py-3 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            {getActionLabel()}
          </button>
        </div>
      )}
    </div>
  );
}
```

**Step 2: Commit**

```bash
jj describe -m "feat: add LessonOverview component"
```

---

## Task 4: Frontend - ModuleSidebar Component

Create the accordion sidebar showing modules and lessons.

**Files:**
- Create: `web_frontend/src/components/course/ModuleSidebar.tsx`

**Step 1: Create the component**

Create `web_frontend/src/components/course/ModuleSidebar.tsx`:

```typescript
/**
 * Accordion sidebar showing course modules and lessons.
 */

import { useState, useEffect } from "react";
import type { ModuleInfo, LessonInfo } from "../../types/course";
import { ChevronDown, ChevronRight, Check, Circle } from "lucide-react";

type ModuleSidebarProps = {
  courseTitle: string;
  modules: ModuleInfo[];
  selectedLessonId: string | null;
  onLessonSelect: (lesson: LessonInfo) => void;
};

function LessonStatusIcon({ status }: { status: LessonInfo["status"] }) {
  if (status === "completed") {
    return <Check className="w-4 h-4 text-blue-500" />;
  }
  if (status === "in_progress") {
    return <Circle className="w-4 h-4 text-blue-500 fill-blue-500" />;
  }
  return <Circle className="w-4 h-4 text-slate-300" />;
}

export default function ModuleSidebar({
  courseTitle,
  modules,
  selectedLessonId,
  onLessonSelect,
}: ModuleSidebarProps) {
  // Track which modules are expanded
  const [expandedModules, setExpandedModules] = useState<Set<string>>(new Set());

  // Auto-expand module containing selected lesson on mount
  useEffect(() => {
    if (selectedLessonId) {
      for (const module of modules) {
        if (module.lessons.some((l) => l.id === selectedLessonId)) {
          setExpandedModules((prev) => new Set(prev).add(module.id));
          break;
        }
      }
    }
  }, [selectedLessonId, modules]);

  const toggleModule = (moduleId: string) => {
    setExpandedModules((prev) => {
      const next = new Set(prev);
      if (next.has(moduleId)) {
        next.delete(moduleId);
      } else {
        next.add(moduleId);
      }
      return next;
    });
  };

  const getModuleProgress = (module: ModuleInfo) => {
    const completed = module.lessons.filter((l) => l.status === "completed").length;
    return `${completed}/${module.lessons.length}`;
  };

  return (
    <div className="h-full flex flex-col bg-slate-50 border-r border-slate-200">
      {/* Course title */}
      <div className="p-4 border-b border-slate-200">
        <h1 className="text-lg font-bold text-slate-900">{courseTitle}</h1>
      </div>

      {/* Modules list */}
      <div className="flex-1 overflow-y-auto">
        {modules.map((module) => {
          const isExpanded = expandedModules.has(module.id);

          return (
            <div key={module.id} className="border-b border-slate-200">
              {/* Module header */}
              <button
                onClick={() => toggleModule(module.id)}
                className="w-full flex items-center gap-2 p-4 hover:bg-slate-100 transition-colors text-left"
              >
                {isExpanded ? (
                  <ChevronDown className="w-4 h-4 text-slate-500 flex-shrink-0" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-slate-500 flex-shrink-0" />
                )}
                <span className="flex-1 font-medium text-slate-900">{module.title}</span>
                <span className="text-sm text-slate-500">{getModuleProgress(module)}</span>
              </button>

              {/* Lessons list */}
              {isExpanded && (
                <div className="pb-2">
                  {module.lessons.map((lesson) => {
                    const isSelected = lesson.id === selectedLessonId;

                    return (
                      <button
                        key={lesson.id}
                        onClick={() => onLessonSelect(lesson)}
                        className={`w-full flex items-center gap-3 px-4 py-2 pl-10 text-left transition-colors ${
                          isSelected
                            ? "bg-blue-50 text-blue-900"
                            : "hover:bg-slate-100 text-slate-700"
                        }`}
                      >
                        <LessonStatusIcon status={lesson.status} />
                        <span className="flex-1 text-sm">{lesson.title}</span>
                        {lesson.status === "in_progress" && (
                          <span className="text-xs text-blue-600 font-medium">Continue</span>
                        )}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
```

**Step 2: Commit**

```bash
jj describe -m "feat: add ModuleSidebar component"
```

---

## Task 5: Frontend - CourseOverviewPage

Create the main page component with two-panel layout.

**Files:**
- Create: `web_frontend/src/pages/CourseOverview.tsx`
- Modify: `web_frontend/src/App.tsx` (add route)

**Step 1: Create the page component**

Create `web_frontend/src/pages/CourseOverview.tsx`:

```typescript
/**
 * Course overview page with two-panel layout.
 * Sidebar shows modules/lessons, main panel shows selected lesson details.
 */

import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import { getCourseProgress } from "../api/lessons";
import type { CourseProgress, LessonInfo } from "../types/course";
import ModuleSidebar from "../components/course/ModuleSidebar";
import LessonOverview from "../components/course/LessonOverview";

export default function CourseOverview() {
  const { courseId = "default" } = useParams();
  const navigate = useNavigate();

  const [courseProgress, setCourseProgress] = useState<CourseProgress | null>(null);
  const [selectedLesson, setSelectedLesson] = useState<LessonInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load course progress
  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const data = await getCourseProgress(courseId);
        setCourseProgress(data);

        // Auto-select current lesson (first in-progress, or first not-started)
        let currentLesson: LessonInfo | null = null;
        for (const module of data.modules) {
          for (const lesson of module.lessons) {
            if (lesson.status === "in_progress") {
              currentLesson = lesson;
              break;
            }
            if (!currentLesson && lesson.status === "not_started") {
              currentLesson = lesson;
            }
          }
          if (currentLesson?.status === "in_progress") break;
        }
        if (currentLesson) {
          setSelectedLesson(currentLesson);
        } else if (data.modules[0]?.lessons[0]) {
          setSelectedLesson(data.modules[0].lessons[0]);
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load course");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [courseId]);

  const handleStartLesson = () => {
    if (!selectedLesson) return;
    navigate(`/course/${courseId}/lesson/${selectedLesson.id}`);
  };

  const handleStageClick = (index: number) => {
    // Open preview modal for article/video stages
    // For now, just navigate to the lesson
    if (selectedLesson) {
      navigate(`/course/${courseId}/lesson/${selectedLesson.id}`);
    }
  };

  // Find module for breadcrumb
  const selectedModule = courseProgress?.modules.find((m) =>
    m.lessons.some((l) => l.id === selectedLesson?.id)
  );

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-slate-500">Loading course...</div>
      </div>
    );
  }

  if (error || !courseProgress) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-red-500">{error || "Course not found"}</div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-white">
      {/* Breadcrumb */}
      <div className="border-b border-slate-200 px-6 py-3 flex items-center gap-2 text-sm">
        <a href="/" className="text-slate-500 hover:text-slate-700">
          Home
        </a>
        <ChevronRight className="w-4 h-4 text-slate-400" />
        <span className="text-slate-700 font-medium">{courseProgress.course.title}</span>
        {selectedModule && (
          <>
            <ChevronRight className="w-4 h-4 text-slate-400" />
            <span className="text-slate-500">{selectedModule.title}</span>
          </>
        )}
        {selectedLesson && (
          <>
            <ChevronRight className="w-4 h-4 text-slate-400" />
            <span className="text-slate-900">{selectedLesson.title}</span>
          </>
        )}
      </div>

      {/* Two-panel layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <div className="w-72 flex-shrink-0">
          <ModuleSidebar
            courseTitle={courseProgress.course.title}
            modules={courseProgress.modules}
            selectedLessonId={selectedLesson?.id ?? null}
            onLessonSelect={setSelectedLesson}
          />
        </div>

        {/* Main panel */}
        <div className="flex-1 p-8 overflow-y-auto">
          {selectedLesson ? (
            <LessonOverview
              lessonTitle={selectedLesson.title}
              stages={selectedLesson.stages}
              status={selectedLesson.status}
              currentStageIndex={selectedLesson.currentStageIndex}
              onStageClick={handleStageClick}
              onStartLesson={handleStartLesson}
            />
          ) : (
            <div className="text-slate-500">Select a lesson to view details</div>
          )}
        </div>
      </div>
    </div>
  );
}
```

**Step 2: Add route to App.tsx**

In `web_frontend/src/App.tsx`, add the import and route:

```typescript
import CourseOverview from "./pages/CourseOverview";
```

Add the route inside the Routes, before the Layout routes (since it's full-screen):

```typescript
<Route path="/course/:courseId" element={<CourseOverview />} />
<Route path="/course" element={<CourseOverview />} />
```

**Step 3: Test manually**

```bash
# Navigate to http://localhost:5173/course/default
```

Expected: Two-panel layout with sidebar showing modules and main panel showing lesson stages.

**Step 4: Commit**

```bash
jj describe -m "feat: add CourseOverview page"
```

---

## Task 6: Frontend - Content Preview Modal

Add modal to preview article/video content from the course overview.

**Files:**
- Create: `web_frontend/src/components/course/ContentPreviewModal.tsx`
- Modify: `web_frontend/src/pages/CourseOverview.tsx` (integrate modal)

**Step 1: Create the modal component**

Create `web_frontend/src/components/course/ContentPreviewModal.tsx`:

```typescript
/**
 * Modal for previewing article/video content from course overview.
 */

import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { getLesson, getSession, createSession } from "../../api/lessons";
import ContentPanel from "../unified-lesson/ContentPanel";
import type { Stage, ArticleData } from "../../types/unified-lesson";

type ContentPreviewModalProps = {
  lessonId: string;
  stageIndex: number;
  sessionId: number | null;
  onClose: () => void;
};

export default function ContentPreviewModal({
  lessonId,
  stageIndex,
  sessionId,
  onClose,
}: ContentPreviewModalProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stage, setStage] = useState<Stage | null>(null);
  const [article, setArticle] = useState<ArticleData | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);

        // Get lesson to find stage type
        const lesson = await getLesson(lessonId);
        const targetStage = lesson.stages[stageIndex];

        if (!targetStage || targetStage.type === "chat") {
          setError("Cannot preview this content");
          return;
        }

        setStage(targetStage);

        // Get content via session API
        let sid = sessionId;
        if (!sid) {
          // Create temporary session to get content
          sid = await createSession(lessonId);
        }

        const session = await getSession(sid, stageIndex);
        setArticle(session.article);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load content");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [lessonId, stageIndex, sessionId]);

  // Close on escape
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      {/* Modal */}
      <div className="relative w-full max-w-4xl max-h-[90vh] bg-white rounded-lg shadow-xl flex flex-col mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-200">
          <h3 className="text-lg font-medium text-slate-900">
            {stage?.type === "article" ? "Article Preview" : "Video Preview"}
          </h3>
          <button
            onClick={onClose}
            className="p-1 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-slate-500" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {loading && <div className="text-slate-500">Loading...</div>}
          {error && <div className="text-red-500">{error}</div>}
          {!loading && !error && stage && (
            <ContentPanel
              stage={stage}
              article={article}
              onComplete={() => {}}
              isComplete={true}
            />
          )}
        </div>
      </div>
    </div>
  );
}
```

**Step 2: Integrate modal into CourseOverview**

Add state and modal to `CourseOverview.tsx`:

```typescript
// Add import
import ContentPreviewModal from "../components/course/ContentPreviewModal";

// Add state (after other useState calls)
const [previewStage, setPreviewStage] = useState<{ lessonId: string; stageIndex: number; sessionId: number | null } | null>(null);

// Update handleStageClick
const handleStageClick = (index: number) => {
  if (!selectedLesson) return;
  const stage = selectedLesson.stages[index];
  if (stage.type === "chat") return; // Can't preview chat
  setPreviewStage({
    lessonId: selectedLesson.id,
    stageIndex: index,
    sessionId: selectedLesson.sessionId,
  });
};

// Add modal before closing div of return
{previewStage && (
  <ContentPreviewModal
    lessonId={previewStage.lessonId}
    stageIndex={previewStage.stageIndex}
    sessionId={previewStage.sessionId}
    onClose={() => setPreviewStage(null)}
  />
)}
```

**Step 3: Test manually**

Click on an article or video stage in the lesson overview. Modal should appear with content.

**Step 4: Commit**

```bash
jj describe -m "feat: add content preview modal for course overview"
```

---

## Task 7: Frontend - LessonDrawer for Player

Create slide-out drawer component for the lesson player.

**Files:**
- Create: `web_frontend/src/components/unified-lesson/LessonDrawer.tsx`

**Step 1: Create the drawer component**

Create `web_frontend/src/components/unified-lesson/LessonDrawer.tsx`:

```typescript
/**
 * Slide-out drawer showing lesson overview in the player.
 * Slides in from the right, ~40% width, floats over content.
 */

import { useEffect } from "react";
import { X, List } from "lucide-react";
import type { StageInfo, LessonStatus } from "../../types/course";
import LessonOverview from "../course/LessonOverview";

type LessonDrawerProps = {
  isOpen: boolean;
  onClose: () => void;
  lessonTitle: string;
  stages: StageInfo[];
  currentStageIndex: number;
  onStageClick: (index: number) => void;
};

export default function LessonDrawer({
  isOpen,
  onClose,
  lessonTitle,
  stages,
  currentStageIndex,
  onStageClick,
}: LessonDrawerProps) {
  // Close on escape
  useEffect(() => {
    if (!isOpen) return;
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/20 z-40 transition-opacity"
          onClick={onClose}
        />
      )}

      {/* Drawer */}
      <div
        className={`fixed top-0 right-0 h-full w-[40%] max-w-md bg-white shadow-xl z-50 transform transition-transform duration-300 ease-out ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-200">
          <h3 className="text-lg font-medium text-slate-900">Lesson Overview</h3>
          <button
            onClick={onClose}
            className="p-1 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-slate-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 h-[calc(100%-4rem)] overflow-y-auto">
          <LessonOverview
            lessonTitle={lessonTitle}
            stages={stages}
            status="in_progress"
            currentStageIndex={currentStageIndex}
            onStageClick={onStageClick}
            showActions={false}
          />
        </div>
      </div>
    </>
  );
}

/**
 * Button to toggle the drawer, shown in player header.
 */
export function LessonDrawerToggle({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
      title="Lesson Overview"
    >
      <List className="w-5 h-5 text-slate-600" />
    </button>
  );
}
```

**Step 2: Commit**

```bash
jj describe -m "feat: add LessonDrawer component for player"
```

---

## Task 8: Integrate LessonDrawer into UnifiedLesson

Add the drawer toggle and drawer to the lesson player.

**Files:**
- Modify: `web_frontend/src/pages/UnifiedLesson.tsx`

**Step 1: Read current UnifiedLesson to understand structure**

Review the file to find where to add the drawer toggle (likely in header area) and drawer component.

**Step 2: Add imports**

Add at top of `UnifiedLesson.tsx`:

```typescript
import LessonDrawer, { LessonDrawerToggle } from "../components/unified-lesson/LessonDrawer";
import type { StageInfo } from "../types/course";
```

**Step 3: Add state for drawer**

Add state variable:

```typescript
const [drawerOpen, setDrawerOpen] = useState(false);
```

**Step 4: Convert stages to StageInfo format**

Add helper to convert session stages to StageInfo format:

```typescript
const stagesForDrawer: StageInfo[] = sessionState?.stages.map((s) => ({
  type: s.type,
  title: s.type === "chat" ? "Discussion" : (s.title || s.type),
  duration: s.type === "video" ? `${Math.ceil((s.to - s.from) / 60)} min` : s.type === "article" ? "Article" : null,
  optional: s.optional ?? false,
})) ?? [];
```

**Step 5: Add drawer toggle to header**

Find the header section and add the toggle button. The exact location depends on the current header structure.

**Step 6: Add drawer component**

Add before the closing tag of the main container:

```typescript
<LessonDrawer
  isOpen={drawerOpen}
  onClose={() => setDrawerOpen(false)}
  lessonTitle={sessionState?.lesson_title ?? ""}
  stages={stagesForDrawer}
  currentStageIndex={sessionState?.current_stage_index ?? 0}
  onStageClick={(index) => {
    // Navigate to stage (same as progress bar click)
    handleStageClick(index, sessionState?.stages[index]);
    setDrawerOpen(false);
  }}
/>
```

**Step 7: Test manually**

Open a lesson, click the drawer toggle, verify drawer slides in and stages are clickable.

**Step 8: Commit**

```bash
jj describe -m "feat: integrate LessonDrawer into UnifiedLesson player"
```

---

## Task 9: Export get_stage_title from lessons

The backend endpoint uses `get_stage_title` but it's defined in `web_api/routes/lessons.py`. Move it to core and export.

**Files:**
- Modify: `core/lessons/content.py` (add function)
- Modify: `core/lessons/__init__.py` (export)
- Modify: `web_api/routes/lessons.py` (import from core)

**Step 1: Add function to content.py**

Add to `core/lessons/content.py`:

```python
def get_stage_title(stage) -> str:
    """Extract display title from a stage using actual content metadata."""
    from .types import ArticleStage, VideoStage

    if isinstance(stage, ArticleStage):
        try:
            result = load_article_with_metadata(stage.source)
            return result.metadata.title or "Article"
        except FileNotFoundError:
            return "Article"
    elif isinstance(stage, VideoStage):
        try:
            result = load_video_transcript_with_metadata(stage.source)
            return result.metadata.title or "Video"
        except FileNotFoundError:
            return "Video"
    return "Discussion"
```

**Step 2: Export from __init__.py**

Add `get_stage_title` to the exports in `core/lessons/__init__.py`.

**Step 3: Update lessons.py import**

In `web_api/routes/lessons.py`, import from core instead of defining locally:

```python
from core.lessons import (
    # ... existing imports ...
    get_stage_title,
)
```

Remove the local `get_stage_title` function definition.

**Step 4: Commit**

```bash
jj describe -m "refactor: move get_stage_title to core/lessons"
```

---

## Summary

After completing all tasks, you'll have:

1. **Backend endpoint** `GET /api/courses/:courseId/progress` returning course structure + user progress
2. **CourseOverview page** at `/course/:courseId` with two-panel layout
3. **ModuleSidebar** accordion component showing modules and lessons with progress
4. **LessonOverview** reusable component showing vertical stage list with progress line
5. **ContentPreviewModal** for previewing articles/videos from course overview
6. **LessonDrawer** slide-out panel in the lesson player

The components are designed to be reusable, with LessonOverview appearing in both the course overview main panel and the in-player drawer.
