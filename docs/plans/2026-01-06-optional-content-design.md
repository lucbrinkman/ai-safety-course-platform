# Optional Content & Stage Previewing

## Overview

Add support for optional readings/videos that learners can skip, and allow previewing upcoming stages.

### Goals
1. Allow previewing upcoming stages (grayed out but clickable)
2. Add optional readings/videos that learners can skip

### Non-goals (this iteration)
- Popup/modal for choosing between multiple optional items
- Lesson-level intro text for optional content
- Per-reading descriptions in the UI

## User Experience

### Stage Previewing
- All stages visible in progress bar from the start
- Past stages: full color, clickable (existing)
- Current stage: highlighted with ring (existing)
- Future stages: grayed out (50% opacity), clickable for preview
- When previewing, content loads but "Done Reading" button is hidden

### Optional Stages
- Optional stages have distinct visual: hollow circle with dotted outline
- When viewing an optional stage at your current position, a banner appears:
  ```
  ┌──────────────────────────────────────────────────────────┐
  │ ℹ️  This reading is optional.        [Skip to next →]   │
  └──────────────────────────────────────────────────────────┘
  ```
- "Skip to next" advances without marking stage complete
- Banner is static (above content, scrolls with content), always visible while on optional stage

### Progress Bar Visual States

| State | Required Stage | Optional Stage |
|-------|----------------|----------------|
| Completed | Filled circle, full opacity | Filled circle, dotted outline, full opacity |
| Current (viewing) | Filled circle + ring | Filled circle, dotted outline + ring |
| Future (not viewing) | Filled circle, 50% opacity | Hollow circle, dotted outline, 50% opacity |
| Future (viewing/preview) | Filled circle, 50% opacity + ring | Filled circle, dotted outline, 50% opacity + ring |

## YAML Schema

```yaml
stages:
  - type: article
    source: articles/main-reading.md

  # Optional flag works on article and video stages
  - type: article
    source: articles/deep-dive.md
    optional: true

  - type: video
    source: video_transcripts/bonus-talk.md
    optional: true

  - type: chat
    instructions: ...
    # Note: chat stages cannot be optional
```

**Validation:**
- `optional` is boolean, defaults to `false`
- Only valid on `article` and `video` stages
- Error if `optional: true` on `chat` stage

## Backend Changes

### `core/lessons/types.py`

Add `optional` field to ArticleStage and VideoStage:

```python
@dataclass
class ArticleStage:
    type: Literal["article"]
    source: str
    from_anchor: str | None = None
    to_anchor: str | None = None
    optional: bool = False  # NEW

@dataclass
class VideoStage:
    type: Literal["video"]
    source: str
    from_time: str | None = None
    to_time: str | None = None
    optional: bool = False  # NEW

# ChatStage unchanged (no optional field)
```

### `core/lessons/loader.py`

- Parse `optional` from YAML, default to `False`
- Validate: error if `optional: true` on chat stage

### API Routes

No changes needed - `optional` field will be included in stage data returned to frontend.

## Frontend Changes

### 1. `StageProgressBar.tsx`

**Remove future click restriction** (~line 67-72):
```typescript
// REMOVE THIS:
if (index > currentStageIndex) {
  return; // Don't allow clicking future stages
}
```

**Add styling for optional and future stages:**
```css
/* Future stages */
.stage-indicator-future {
  opacity: 0.5;
}

/* Optional stages (not viewing) */
.stage-indicator-optional {
  background: transparent;
  border: 2px dotted currentColor;
}

/* Optional stages (viewing or completed) */
.stage-indicator-optional.viewing,
.stage-indicator-optional.completed {
  background: currentColor;
  border: 2px dotted currentColor;
}
```

### 2. New `OptionalBanner.tsx`

```typescript
interface OptionalBannerProps {
  onSkip: () => void;
}

export function OptionalBanner({ onSkip }: OptionalBannerProps) {
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <InfoIcon className="w-4 h-4 text-blue-500" />
        <span className="text-sm text-blue-700">This reading is optional.</span>
      </div>
      <button
        onClick={onSkip}
        className="text-sm text-blue-600 hover:text-blue-800 font-medium"
      >
        Skip to next →
      </button>
    </div>
  );
}
```

### 3. `ContentPanel.tsx`

Add props and render banner:
```typescript
interface ContentPanelProps {
  // ... existing props
  isOptional?: boolean;
  onSkip?: () => void;
}

// In render, above article/video content:
{isOptional && viewingStageIndex === currentStageIndex && (
  <OptionalBanner onSkip={onSkip} />
)}
```

### 4. `UnifiedLesson.tsx`

Wire up the skip handler:
```typescript
const handleSkipOptional = useCallback(async () => {
  if (!sessionId) return;
  await advanceStage(sessionId);
  // Session will refresh with new current_stage_index
}, [sessionId]);
```

Pass to ContentPanel:
```typescript
<ContentPanel
  // ... existing props
  isOptional={currentStage?.optional ?? false}
  onSkip={handleSkipOptional}
/>
```

## Implementation Order

1. **Stage previewing** (enables clicking future stages)
   - Update `StageProgressBar.tsx` to allow future clicks
   - Add grayed-out styling for future stages
   - Test: can click future stage, content loads, "Done Reading" hidden

2. **Backend optional support**
   - Add `optional` field to types
   - Update loader to parse field
   - Add validation (no optional chat)
   - Test: YAML with optional stages loads correctly

3. **Frontend optional support**
   - Add dotted outline styling for optional stages
   - Create `OptionalBanner` component
   - Wire up skip handler
   - Test: optional stage shows banner, skip advances

## Test Cases

### Stage Previewing
- [ ] Future stages are visible but grayed out
- [ ] Clicking future stage loads its content
- [ ] "Done Reading" hidden when previewing future
- [ ] Clicking back to current stage restores normal state

### Optional Stages
- [ ] Optional stages show hollow/dotted indicator
- [ ] Banner appears on optional stage (when current)
- [ ] Banner hidden when previewing optional stage
- [ ] "Skip to next" advances to next stage
- [ ] Skipped optional stages don't block progression
- [ ] YAML validation rejects `optional: true` on chat stages
