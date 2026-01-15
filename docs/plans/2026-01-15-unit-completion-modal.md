# Unit Completion Modal Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Show "This was the last lesson of Unit X" when user completes a lesson and the next progression item is a meeting, instead of showing "Next: [lesson]".

**Architecture:** Modify `get_next_lesson` to check what comes next in the course progression. If it's a Meeting, return `completedUnit: N` instead of `nextLessonSlug/Title`. Frontend interprets this and shows unit completion message with only "Return to Course" button.

**Tech Stack:** Python (FastAPI), TypeScript (React), existing course progression system

---

## Background

Course progression structure (from `default.yaml`):
```yaml
progression:
  - lesson: introduction
  - lesson: intro-to-ai-safety
  - meeting: 1                    # <-- Unit 1 boundary
  - lesson: intelligence-feedback-loop
  - meeting: 2                    # <-- Unit 2 boundary
```

"Unit N" = lessons before `meeting: N`. When user completes `intro-to-ai-safety`, the next item is `meeting: 1`, so we show "Unit 1 complete".

---

### Task 1: Update `get_next_lesson` to detect meeting boundaries

**Files:**
- Modify: `core/lessons/course_loader.py:56-78`

**Step 1: Rewrite `get_next_lesson` to use full progression**

Replace the current implementation that flattens to lesson slugs with one that walks the progression:

```python
def get_next_lesson(course_slug: str, current_lesson_slug: str) -> dict | None:
    """Get what comes after the current lesson in the progression.

    Returns:
        - {"type": "lesson", "slug": str, "title": str} if next item is a lesson
        - {"type": "unit_complete", "unit_number": int} if next item is a meeting
        - None if end of course or lesson not found
    """
    course = load_course(course_slug)

    # Find the current lesson's index in progression
    current_index = None
    for i, item in enumerate(course.progression):
        if isinstance(item, LessonRef) and item.slug == current_lesson_slug:
            current_index = i
            break

    if current_index is None:
        return None  # Lesson not in this course

    # Look at the next item in progression
    next_index = current_index + 1
    if next_index >= len(course.progression):
        return None  # End of course

    next_item = course.progression[next_index]

    if isinstance(next_item, Meeting):
        return {"type": "unit_complete", "unit_number": next_item.number}

    if isinstance(next_item, LessonRef):
        try:
            next_lesson = load_lesson(next_item.slug)
            return {
                "type": "lesson",
                "slug": next_item.slug,
                "title": next_lesson.title,
            }
        except LessonNotFoundError:
            return None

    return None
```

**Step 2: Run existing tests to verify no regressions**

Run: `pytest discord_bot/tests/ -v`
Expected: All tests pass (these don't test `get_next_lesson` directly)

**Step 3: Commit**

```bash
jj describe -m "refactor: get_next_lesson returns dict with type field for meeting detection"
```

---

### Task 2: Update API endpoint to return new response shape

**Files:**
- Modify: `web_api/routes/courses.py:27-47`

**Step 1: Update endpoint to handle new return type**

```python
@router.get("/{course_slug}/next-lesson")
async def get_next_lesson_endpoint(
    course_slug: str,
    current: str = Query(..., description="Current lesson slug"),
):
    """Get what comes after the current lesson.

    Returns:
        - 200 with {nextLessonSlug, nextLessonTitle} if next item is a lesson
        - 200 with {completedUnit: N} if next item is a meeting (unit boundary)
        - 204 No Content if end of course
    """
    try:
        result = get_next_lesson(course_slug, current)
    except CourseNotFoundError:
        raise HTTPException(status_code=404, detail=f"Course not found: {course_slug}")

    if result is None:
        return Response(status_code=204)

    if result["type"] == "unit_complete":
        return {"completedUnit": result["unit_number"]}

    # result["type"] == "lesson"
    return {
        "nextLessonSlug": result["slug"],
        "nextLessonTitle": result["title"],
    }
```

**Step 2: Test manually with curl**

```bash
# Start dev server if not running
python main.py --dev --no-bot &

# Test lesson with next lesson
curl "http://localhost:8000/api/courses/default/next-lesson?current=introduction"
# Expected: {"nextLessonSlug":"intro-to-ai-safety","nextLessonTitle":"..."}

# Test lesson before meeting
curl "http://localhost:8000/api/courses/default/next-lesson?current=intro-to-ai-safety"
# Expected: {"completedUnit":1}

# Test last lesson (if applicable)
curl "http://localhost:8000/api/courses/default/next-lesson?current=intelligence-feedback-loop"
# Expected: 204 No Content (or completedUnit if there's a meeting after)
```

**Step 3: Commit**

```bash
jj describe -m "feat(api): next-lesson endpoint returns completedUnit when hitting meeting boundary"
```

---

### Task 3: Update frontend API client

**Files:**
- Modify: `web_frontend/src/api/lessons.ts:194-205`

**Step 1: Update return type and parsing**

```typescript
interface NextLessonResponse {
  nextLessonSlug: string;
  nextLessonTitle: string;
}

interface CompletedUnitResponse {
  completedUnit: number;
}

export type LessonCompletionResult =
  | { type: "next_lesson"; slug: string; title: string }
  | { type: "unit_complete"; unitNumber: number }
  | null;

export async function getNextLesson(
  courseSlug: string,
  currentLessonSlug: string
): Promise<LessonCompletionResult> {
  const res = await fetchWithTimeout(
    `${API_BASE}/api/courses/${courseSlug}/next-lesson?current=${currentLessonSlug}`
  );
  if (!res.ok) throw new Error("Failed to fetch next lesson");
  // 204 No Content means end of course
  if (res.status === 204) return null;

  const data = await res.json();

  if ("completedUnit" in data) {
    return { type: "unit_complete", unitNumber: data.completedUnit };
  }

  return {
    type: "next_lesson",
    slug: data.nextLessonSlug,
    title: data.nextLessonTitle,
  };
}
```

**Step 2: Run TypeScript check**

Run: `cd web_frontend && npx tsc --noEmit`
Expected: Type errors in UnifiedLesson.tsx (will fix in next task)

**Step 3: Commit**

```bash
jj describe -m "feat(frontend): getNextLesson returns discriminated union for lesson vs unit completion"
```

---

### Task 4: Update UnifiedLesson to handle new response type

**Files:**
- Modify: `web_frontend/src/pages/UnifiedLesson.tsx`

**Step 1: Update state type**

Find and update the nextLesson state (around line 82):

```typescript
// Before:
const [nextLesson, setNextLesson] = useState<{
  slug: string;
  title: string;
} | null>(null);

// After:
import type { LessonCompletionResult } from "../api/lessons";
// ...
const [lessonCompletionResult, setLessonCompletionResult] = useState<LessonCompletionResult>(null);
```

**Step 2: Update the effect that fetches next lesson**

Find the effect (around line 631) and update:

```typescript
// Fetch next lesson info when lesson completes (only in course context)
useEffect(() => {
  if (!session?.completed || !courseId || !lessonId) return;

  async function fetchNextLesson() {
    try {
      const result = await getNextLesson(courseId!, lessonId!);
      setLessonCompletionResult(result);
    } catch (e) {
      console.error("Failed to fetch next lesson:", e);
      setLessonCompletionResult(null);
    }
  }

  fetchNextLesson();
}, [session?.completed, courseId, lessonId]);
```

**Step 3: Update modal props**

Find the LessonCompleteModal usage (around line 845) and update:

```typescript
// Derive props for modal from lessonCompletionResult
const nextLesson = lessonCompletionResult?.type === "next_lesson"
  ? { slug: lessonCompletionResult.slug, title: lessonCompletionResult.title }
  : null;
const completedUnit = lessonCompletionResult?.type === "unit_complete"
  ? lessonCompletionResult.unitNumber
  : null;

// In JSX:
<LessonCompleteModal
  isOpen={(session.completed || !session.current_stage) && !completionModalDismissed}
  lessonTitle={session.lesson_title}
  courseId={courseId}
  isInSignupsTable={isInSignupsTable}
  nextLesson={nextLesson}
  completedUnit={completedUnit}
  onClose={() => setCompletionModalDismissed(true)}
/>
```

**Step 4: Run TypeScript check**

Run: `cd web_frontend && npx tsc --noEmit`
Expected: Type error in LessonCompleteModal (completedUnit prop doesn't exist yet)

**Step 5: Commit**

```bash
jj describe -m "feat(UnifiedLesson): handle unit completion result from API"
```

---

### Task 5: Update LessonCompleteModal to show unit completion

**Files:**
- Modify: `web_frontend/src/components/unified-lesson/LessonCompleteModal.tsx`

**Step 1: Add completedUnit prop**

```typescript
interface Props {
  isOpen: boolean;
  lessonTitle?: string;
  courseId?: string;
  isInSignupsTable?: boolean;
  nextLesson?: NextLesson | null;
  completedUnit?: number | null;  // NEW: Unit number if just completed a unit
  onClose?: () => void;
}
```

**Step 2: Update component to handle unit completion**

```typescript
export default function LessonCompleteModal({
  isOpen,
  lessonTitle,
  courseId,
  isInSignupsTable = false,
  nextLesson,
  completedUnit,  // NEW
  onClose,
}: Props) {
  if (!isOpen) return null;

  const isInCourseContext = !!courseId;
  const hasNextLesson = !!nextLesson;
  const hasCompletedUnit = completedUnit != null;  // NEW

  let primaryCta: { label: string; to: string };
  let secondaryCta: { label: string; to: string } | null = null;
  let completionMessage: string;  // NEW

  if (!isInCourseContext) {
    // Standalone lesson context - unchanged
    completionMessage = lessonTitle
      ? `You've finished "${lessonTitle}".`
      : "Great work!";
    if (!isInSignupsTable) {
      primaryCta = { label: "Join the Full Course", to: "/signup" };
      secondaryCta = { label: "View Course", to: "/course" };
    } else {
      primaryCta = { label: "View Course", to: "/course" };
    }
  } else {
    // Course lesson context
    const courseUrl = `/course/${courseId}`;

    if (hasCompletedUnit) {
      // NEW: Unit completion - show special message, only "Return to Course" button
      completionMessage = `This was the last lesson of Unit ${completedUnit}.`;
      primaryCta = { label: "Return to Course", to: courseUrl };
      // No secondary CTA - don't prompt them to go to next unit yet
    } else if (!isInSignupsTable) {
      completionMessage = lessonTitle
        ? `You've finished "${lessonTitle}".`
        : "Great work!";
      primaryCta = { label: "Join the Full Course", to: "/signup" };
      secondaryCta = { label: "Return to Course", to: courseUrl };
    } else if (hasNextLesson) {
      completionMessage = lessonTitle
        ? `You've finished "${lessonTitle}".`
        : "Great work!";
      const nextLessonUrl = `/course/${courseId}/lesson/${nextLesson!.slug}`;
      primaryCta = { label: `Next: ${nextLesson!.title}`, to: nextLessonUrl };
      secondaryCta = { label: "Return to Course", to: courseUrl };
    } else {
      // End of course
      completionMessage = lessonTitle
        ? `You've finished "${lessonTitle}".`
        : "Great work!";
      primaryCta = { label: "Return to Course", to: courseUrl };
    }
  }

  // ... rest of component unchanged, but use completionMessage variable:
  // <p className="text-gray-600 mb-6">
  //   {completionMessage}{" "}
  //   Ready to continue your AI safety journey?
  // </p>
```

**Step 3: Update the message JSX**

Replace the hardcoded message with the variable:

```typescript
<p className="text-gray-600 mb-6">
  {completionMessage}{" "}
  {!hasCompletedUnit && "Ready to continue your AI safety journey?"}
</p>
```

**Step 4: Run TypeScript check**

Run: `cd web_frontend && npx tsc --noEmit`
Expected: PASS

**Step 5: Test in browser**

1. Navigate to `/course/default/lesson/intro-to-ai-safety`
2. Complete the lesson (or skip through stages)
3. Verify modal shows "This was the last lesson of Unit 1." with only "Return to Course" button

**Step 6: Commit**

```bash
jj describe -m "feat(modal): show unit completion message when reaching meeting boundary"
```

---

## Verification Checklist

- [ ] `intro-to-ai-safety` completion shows "Unit 1" message
- [ ] `introduction` completion shows "Next: Intro to AI Safety"
- [ ] Last lesson shows "Return to Course" (end of course)
- [ ] Standalone lessons (`/lesson/:id`) still work unchanged
- [ ] TypeScript compiles without errors
- [ ] No Python syntax errors
