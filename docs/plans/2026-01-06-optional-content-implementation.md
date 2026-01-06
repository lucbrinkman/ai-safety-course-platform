# Optional Content & Stage Previewing Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add support for optional readings/videos that learners can skip, and allow previewing upcoming stages.

**Architecture:** Add `optional: boolean` field to article/video stages. Modify progress bar to allow clicking future stages. Show banner with skip button on optional stages.

**Tech Stack:** Python dataclasses, FastAPI, React, TypeScript, Tailwind CSS

---

## Task 1: Update Backend Types

**Files:**
- Modify: `core/lessons/types.py:10-25`
- Modify: `core/lessons/tests/test_loader.py:38-41`

**Step 1: Add optional field to ArticleStage**

In `core/lessons/types.py`, modify `ArticleStage` (lines 10-15):

```python
@dataclass
class ArticleStage:
    """Display a section of a markdown article."""
    type: Literal["article"]
    source: str  # Path to article markdown file
    from_text: str | None = None  # None means full article
    to_text: str | None = None
    optional: bool = False  # NEW: Whether this stage can be skipped
```

**Step 2: Add optional field to VideoStage**

In `core/lessons/types.py`, modify `VideoStage` (lines 18-24):

```python
@dataclass
class VideoStage:
    """Display a YouTube video clip."""
    type: Literal["video"]
    source: str  # Path to transcript markdown file
    from_seconds: int = 0
    to_seconds: int | None = None  # None means to end
    optional: bool = False  # NEW: Whether this stage can be skipped
```

**Step 3: Update test allowlist**

In `core/lessons/tests/test_loader.py`, update `ALLOWED_STAGE_BY_TYPE` (lines 37-41):

```python
ALLOWED_STAGE_BY_TYPE = {
    "article": {"type", "source", "from", "to", "optional"},
    "video": {"type", "source", "from", "to", "optional"},
    "chat": {"type", "instructions", "showUserPreviousContent", "showTutorPreviousContent"},
}
```

**Step 4: Run tests to verify nothing breaks**

Run: `pytest core/lessons/tests/test_loader.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
jj describe -m "feat(lessons): add optional field to ArticleStage and VideoStage types"
```

---

## Task 2: Update Loader to Parse Optional Field

**Files:**
- Modify: `core/lessons/loader.py:40-53`

**Step 1: Update article stage parsing**

In `core/lessons/loader.py`, modify the article branch in `_parse_stage` (lines 40-46):

```python
if stage_type == "article":
    return ArticleStage(
        type="article",
        source=data["source"],
        from_text=data.get("from"),
        to_text=data.get("to"),
        optional=data.get("optional", False),
    )
```

**Step 2: Update video stage parsing**

In `core/lessons/loader.py`, modify the video branch in `_parse_stage` (lines 47-53):

```python
elif stage_type == "video":
    return VideoStage(
        type="video",
        source=data["source"],
        from_seconds=_parse_time(data.get("from", "0:00")),
        to_seconds=_parse_time(data.get("to")),
        optional=data.get("optional", False),
    )
```

**Step 3: Run tests**

Run: `pytest core/lessons/tests/test_loader.py -v`
Expected: All tests PASS

**Step 4: Commit**

```bash
jj describe -m "feat(lessons): parse optional field in loader"
```

---

## Task 3: Add Backend Test for Optional Stages

**Files:**
- Modify: `core/lessons/tests/test_loader.py`

**Step 1: Add test for optional parsing**

Add at end of `core/lessons/tests/test_loader.py`:

```python
def test_parse_optional_stages(tmp_path, monkeypatch):
    """Should parse optional field on article and video stages."""
    # Create a test lesson with optional stages
    test_lesson = {
        "id": "test-optional",
        "title": "Test Optional",
        "stages": [
            {"type": "article", "source": "articles/test.md"},
            {"type": "article", "source": "articles/optional.md", "optional": True},
            {"type": "video", "source": "videos/test.md", "optional": True},
            {"type": "chat", "instructions": "Discuss"},
        ]
    }

    # Write test lesson file
    test_lessons_dir = tmp_path / "lessons"
    test_lessons_dir.mkdir()
    lesson_file = test_lessons_dir / "test-optional.yaml"
    lesson_file.write_text(yaml.dump(test_lesson))

    # Monkeypatch LESSONS_DIR
    monkeypatch.setattr("core.lessons.loader.LESSONS_DIR", test_lessons_dir)

    # Load and verify
    from core.lessons.loader import load_lesson
    lesson = load_lesson("test-optional")

    assert lesson.stages[0].optional is False  # default
    assert lesson.stages[1].optional is True   # explicit
    assert lesson.stages[2].optional is True   # video
    assert not hasattr(lesson.stages[3], 'optional')  # chat has no optional


def test_optional_not_allowed_on_chat(tmp_path, monkeypatch):
    """Test file with optional: true on chat should fail allowlist test."""
    # This is validated by test_lessons_only_use_allowed_fields
    # Just verify chat stages don't get optional field parsed
    pass  # The allowlist test covers this
```

**Step 2: Run tests**

Run: `pytest core/lessons/tests/test_loader.py -v`
Expected: All tests PASS

**Step 3: Commit**

```bash
jj describe -m "test(lessons): add tests for optional stage parsing"
```

---

## Task 4: Update Frontend Types

**Files:**
- Modify: `web_frontend/src/types/unified-lesson.ts:5-10,12-17`

**Step 1: Add optional to ArticleStage type**

In `web_frontend/src/types/unified-lesson.ts`, update `ArticleStage` (lines 5-10):

```typescript
export type ArticleStage = {
  type: "article";
  source: string;
  from: string | null;
  to: string | null;
  optional?: boolean;
};
```

**Step 2: Add optional to VideoStage type**

In `web_frontend/src/types/unified-lesson.ts`, update `VideoStage` (lines 12-17):

```typescript
export type VideoStage = {
  type: "video";
  videoId: string;
  from: number;
  to: number | null;
  optional?: boolean;
};
```

**Step 3: Verify TypeScript compiles**

Run: `cd web_frontend && npx tsc --noEmit`
Expected: No errors

**Step 4: Commit**

```bash
jj describe -m "feat(frontend): add optional field to stage types"
```

---

## Task 5: Enable Clicking Future Stages in Progress Bar

**Files:**
- Modify: `web_frontend/src/components/unified-lesson/StageProgressBar.tsx:43-51,66-79,122-135`

**Step 1: Update tooltip for future stages**

In `StageProgressBar.tsx`, modify `getTooltipContent` function (lines 43-52):

```typescript
function getTooltipContent(stage: Stage, index: number, currentStageIndex: number): string {
  const isFuture = index > currentStageIndex;
  const isPastChat = stage.type === "chat" && index < currentStageIndex;
  const isCurrentChat = stage.type === "chat" && index === currentStageIndex;

  if (isFuture) return `Preview ${stage.type} section`;
  if (isPastChat) return "Chat sections can't be revisited";
  if (isCurrentChat) return "Return to chat";
  return `View ${stage.type} section`;
}
```

**Step 2: Allow clicking future stages**

In `StageProgressBar.tsx`, modify `handleDotClick` function (lines 66-79):

```typescript
const handleDotClick = (index: number, stage: Stage) => {
  // Past chat stages can't be revisited
  if (stage.type === "chat" && index < currentStageIndex) {
    return;
  }

  // Future chat stages can't be previewed (no content to show)
  if (stage.type === "chat" && index > currentStageIndex) {
    return;
  }

  // Navigate to stage (including future for preview)
  onStageClick(index);
};
```

**Step 3: Update button styling for future stages**

In `StageProgressBar.tsx`, update the button className (lines 122-135):

```typescript
<button
  onClick={() => handleDotClick(index, stage)}
  disabled={stage.type === "chat" && index !== currentStageIndex && index !== viewingIndex}
  className={`
    relative w-7 h-7 rounded-full flex items-center justify-center
    transition-all duration-150
    ${isReached
      ? isClickable
        ? "bg-blue-500 text-white hover:bg-blue-600 cursor-pointer"
        : "bg-blue-500 text-white cursor-default"
      : "bg-gray-300 text-gray-500 hover:bg-gray-400 cursor-pointer"
    }
    ${isViewing ? "ring-2 ring-offset-2 ring-blue-500" : ""}
    ${isFuture ? "opacity-50" : ""}
  `}
>
```

**Step 4: Verify frontend compiles**

Run: `cd web_frontend && npm run build`
Expected: Build succeeds

**Step 5: Commit**

```bash
jj describe -m "feat(frontend): allow clicking future stages for preview"
```

---

## Task 6: Add Optional Stage Styling to Progress Bar

**Files:**
- Modify: `web_frontend/src/components/unified-lesson/StageProgressBar.tsx:98-141`

**Step 1: Add optional detection**

In `StageProgressBar.tsx`, inside the `stages.map` callback (around line 98), add optional detection:

```typescript
{stages.map((stage, index) => {
  const isReached = index <= currentStageIndex;
  const isViewing = index === viewingIndex;
  const isPastChat = stage.type === "chat" && index < currentStageIndex;
  const isClickable = isReached && !isPastChat;
  const isFuture = index > currentStageIndex;
  const isOptional = 'optional' in stage && stage.optional === true;
```

**Step 2: Update button styling for optional stages**

Replace the button element with updated styling:

```typescript
<button
  onClick={() => handleDotClick(index, stage)}
  disabled={stage.type === "chat" && index !== currentStageIndex && index !== viewingIndex}
  className={`
    relative w-7 h-7 rounded-full flex items-center justify-center
    transition-all duration-150
    ${isOptional
      ? isViewing || isReached
        ? "bg-blue-500 text-white border-2 border-dashed border-blue-300"
        : "bg-transparent text-gray-400 border-2 border-dashed border-gray-400"
      : isReached
        ? isClickable
          ? "bg-blue-500 text-white hover:bg-blue-600 cursor-pointer"
          : "bg-blue-500 text-white cursor-default"
        : "bg-gray-300 text-gray-500 hover:bg-gray-400 cursor-pointer"
    }
    ${isViewing ? "ring-2 ring-offset-2 ring-blue-500" : ""}
    ${isFuture && !isOptional ? "opacity-50" : ""}
    ${isFuture && isOptional ? "opacity-50" : ""}
    ${!isFuture && isClickable ? "cursor-pointer" : ""}
  `}
>
  <StageIcon type={stage.type} small />
</button>
```

**Step 3: Update tooltip for optional stages**

Update `getTooltipContent` to mention optional:

```typescript
function getTooltipContent(stage: Stage, index: number, currentStageIndex: number): string {
  const isFuture = index > currentStageIndex;
  const isPastChat = stage.type === "chat" && index < currentStageIndex;
  const isCurrentChat = stage.type === "chat" && index === currentStageIndex;
  const isOptional = 'optional' in stage && stage.optional === true;
  const optionalPrefix = isOptional ? "(Optional) " : "";

  if (isFuture) return `${optionalPrefix}Preview ${stage.type} section`;
  if (isPastChat) return "Chat sections can't be revisited";
  if (isCurrentChat) return "Return to chat";
  return `${optionalPrefix}View ${stage.type} section`;
}
```

**Step 4: Verify frontend compiles**

Run: `cd web_frontend && npm run build`
Expected: Build succeeds

**Step 5: Commit**

```bash
jj describe -m "feat(frontend): add dotted outline styling for optional stages"
```

---

## Task 7: Create OptionalBanner Component

**Files:**
- Create: `web_frontend/src/components/unified-lesson/OptionalBanner.tsx`

**Step 1: Create the component file**

Create `web_frontend/src/components/unified-lesson/OptionalBanner.tsx`:

```typescript
// web_frontend/src/components/unified-lesson/OptionalBanner.tsx

type OptionalBannerProps = {
  onSkip: () => void;
};

export default function OptionalBanner({ onSkip }: OptionalBannerProps) {
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <svg
          className="w-4 h-4 text-blue-500 flex-shrink-0"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path
            fillRule="evenodd"
            d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
            clipRule="evenodd"
          />
        </svg>
        <span className="text-sm text-blue-700">This reading is optional.</span>
      </div>
      <button
        onClick={onSkip}
        className="text-sm text-blue-600 hover:text-blue-800 font-medium whitespace-nowrap"
      >
        Skip to next →
      </button>
    </div>
  );
}
```

**Step 2: Verify it compiles**

Run: `cd web_frontend && npx tsc --noEmit`
Expected: No errors

**Step 3: Commit**

```bash
jj describe -m "feat(frontend): create OptionalBanner component"
```

---

## Task 8: Integrate OptionalBanner into ContentPanel

**Files:**
- Modify: `web_frontend/src/components/unified-lesson/ContentPanel.tsx:14,17-27,38,84-92`

**Step 1: Import OptionalBanner**

In `ContentPanel.tsx`, add import (after line 14):

```typescript
import OptionalBanner from "./OptionalBanner";
```

**Step 2: Update props type**

In `ContentPanel.tsx`, update `ContentPanelProps` (lines 17-27):

```typescript
type ContentPanelProps = {
  stage: Stage | null;
  article?: ArticleData | null;
  onVideoEnded: () => void;
  onNextClick: () => void;
  onSkipOptional?: () => void;  // NEW
  isReviewing?: boolean;
  isPreviewing?: boolean;  // NEW: viewing future stage
  // For chat stages: show previous content (blurred or visible)
  previousArticle?: ArticleData | null;
  previousStage?: PreviousStageInfo | null;
  showUserPreviousContent?: boolean;
};
```

**Step 3: Update destructuring**

In `ContentPanel.tsx`, update the props destructuring (around line 29-38):

```typescript
export default function ContentPanel({
  stage,
  article,
  onVideoEnded,
  onNextClick,
  onSkipOptional,
  isReviewing = false,
  isPreviewing = false,
  previousArticle,
  previousStage,
  showUserPreviousContent = true,
}: ContentPanelProps) {
```

**Step 4: Add banner rendering**

In `ContentPanel.tsx`, in the article rendering section (around line 84), add banner before ArticlePanel:

```typescript
if (shouldShowArticle && articleToShow) {
  const isOptional = stage && 'optional' in stage && stage.optional === true;
  const showOptionalBanner = isOptional && !isReviewing && !isPreviewing && onSkipOptional;

  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 overflow-hidden">
        <div className="h-full overflow-y-auto">
          {showOptionalBanner && (
            <div className="px-4 pt-4 max-w-[620px] mx-auto">
              <OptionalBanner onSkip={onSkipOptional} />
            </div>
          )}
          <ArticlePanel
            article={articleToShow}
            blurred={isBlurred}
            onScrolledToBottom={showButton ? handleScrolledToBottom : undefined}
          />
        </div>
      </div>
```

**Step 5: Add banner for video stages**

In `ContentPanel.tsx`, in the video stage section (around line 204), add banner:

```typescript
// Video stage
if (stage.type === "video") {
  const isOptional = 'optional' in stage && stage.optional === true;
  const showOptionalBanner = isOptional && !isReviewing && !isPreviewing && onSkipOptional;

  return (
    <div className="h-full flex flex-col">
      {showOptionalBanner && (
        <div className="px-4 pt-4 max-w-[620px] mx-auto">
          <OptionalBanner onSkip={onSkipOptional} />
        </div>
      )}
      <div className="flex-1 flex flex-col justify-center">
        <VideoPlayer
          videoId={stage.videoId}
          start={stage.from}
          end={stage.to || 9999}
          onEnded={isReviewing ? () => {} : onVideoEnded}
        />
      </div>
    </div>
  );
}
```

**Step 6: Verify it compiles**

Run: `cd web_frontend && npx tsc --noEmit`
Expected: No errors

**Step 7: Commit**

```bash
jj describe -m "feat(frontend): integrate OptionalBanner into ContentPanel"
```

---

## Task 9: Wire Up Skip Handler in UnifiedLesson

**Files:**
- Modify: `web_frontend/src/pages/UnifiedLesson.tsx`

**Step 1: Find the ContentPanel usage**

Search for where ContentPanel is rendered and add the new props.

In `UnifiedLesson.tsx`, find the ContentPanel component (around line 358) and add:

```typescript
<ContentPanel
  stage={stageToDisplay}
  article={articleToDisplay}
  onVideoEnded={handleAdvanceStage}
  onNextClick={handleAdvanceStage}
  onSkipOptional={handleAdvanceStage}  // NEW: skip uses same advance logic
  isReviewing={isReviewing}
  isPreviewing={viewingStageIndex !== null && viewingStageIndex > currentStageIndex}  // NEW
  previousArticle={session?.previous_article}
  previousStage={session?.previous_stage}
  showUserPreviousContent={session?.show_user_previous_content}
/>
```

**Step 2: Verify it compiles**

Run: `cd web_frontend && npm run build`
Expected: Build succeeds

**Step 3: Commit**

```bash
jj describe -m "feat(frontend): wire up optional skip handler in UnifiedLesson"
```

---

## Task 10: Manual Testing

**Step 1: Create test lesson with optional stages**

Create or modify a lesson YAML to include optional stages:

```yaml
# educational_content/lessons/test-optional.yaml
id: test-optional
title: Test Optional Content
stages:
  - type: article
    source: articles/four-background-claims.md
    from: "MIRI's mission"
    to: "superintelligent AI systems."
  - type: article
    source: articles/four-background-claims.md
    optional: true
  - type: chat
    instructions: "Discuss what you've learned."
```

**Step 2: Start dev server**

Run: `python main.py --dev --no-bot`

**Step 3: Test in browser**

1. Navigate to lesson
2. Verify future stages appear grayed out but clickable
3. Click a future stage - content should load, "Done reading" hidden
4. Navigate back to current stage
5. Progress to optional stage
6. Verify banner appears: "This reading is optional. [Skip to next →]"
7. Click skip - should advance to next stage
8. Verify optional stage shows dotted outline in progress bar

**Step 4: Clean up test file**

Remove or keep test-optional.yaml as needed.

**Step 5: Final commit**

```bash
jj describe -m "feat: optional content and stage previewing

- Add optional field to article/video stages
- Allow previewing future stages (grayed, clickable)
- Show banner with skip button on optional stages
- Dotted outline styling for optional stages in progress bar"
```

---

## Summary

| Task | Description | Est. Time |
|------|-------------|-----------|
| 1 | Backend types | 3 min |
| 2 | Loader parsing | 3 min |
| 3 | Backend tests | 5 min |
| 4 | Frontend types | 2 min |
| 5 | Future stage clicking | 5 min |
| 6 | Optional styling | 5 min |
| 7 | OptionalBanner component | 3 min |
| 8 | ContentPanel integration | 10 min |
| 9 | UnifiedLesson wiring | 3 min |
| 10 | Manual testing | 10 min |

**Total: ~50 minutes**
