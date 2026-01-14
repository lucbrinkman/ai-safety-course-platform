# Availability Date Range Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Show course date range on the availability selector so users know which dates to check their calendar for.

**Architecture:** Add `duration_days` to the cohort API response, pass selected cohort to AvailabilityStep, calculate end date as `start_date + duration_days - 1`, display friendly message.

**Tech Stack:** Python/FastAPI backend, React/TypeScript frontend

---

## Task 1: Add duration_days to cohort API response

**Files:**
- Modify: `core/queries/cohorts.py:133-143`

**Step 1: Update the select statement to include duration_days**

In `get_available_cohorts`, add `cohorts.c.duration_days` to the select:

```python
# Get all future active cohorts
query = (
    select(
        cohorts.c.cohort_id,
        cohorts.c.cohort_name,
        cohorts.c.cohort_start_date,
        cohorts.c.course_slug,
        cohorts.c.duration_days,
    )
    .where(cohorts.c.cohort_start_date > today)
    .where(cohorts.c.status == "active")
    .order_by(cohorts.c.cohort_start_date)
)
```

**Step 2: Verify manually**

Run: `python main.py --dev --no-bot`
Test: Check browser Network tab for `/api/cohorts/available` response includes `duration_days`

**Step 3: Commit**

```bash
jj new -m "feat: include duration_days in cohort API response"
```

---

## Task 2: Update TypeScript Cohort interface

**Files:**
- Modify: `web_frontend/src/types/signup.ts:14-20`

**Step 1: Add duration_days to Cohort interface**

```typescript
export interface Cohort {
  cohort_id: number;
  cohort_name: string;
  cohort_start_date: string;
  course_name: string;
  duration_days: number;
  role?: string;
}
```

**Step 2: Commit**

```bash
jj new -m "feat: add duration_days to Cohort type"
```

---

## Task 3: Pass selected cohort to AvailabilityStep

**Files:**
- Modify: `web_frontend/src/components/signup/SignupWizard.tsx:235-248`
- Modify: `web_frontend/src/components/signup/AvailabilityStep.tsx:5-11`

**Step 1: Update AvailabilityStep props interface**

In `AvailabilityStep.tsx`, add `cohort` prop:

```typescript
interface AvailabilityStepProps {
  availability: AvailabilityData;
  onAvailabilityChange: (data: AvailabilityData) => void;
  timezone: string;
  onTimezoneChange: (timezone: string) => void;
  onBack: () => void;
  onSubmit: () => void;
  cohort: { cohort_start_date: string; duration_days: number } | null;
}
```

**Step 2: Update AvailabilityStep function signature**

```typescript
export default function AvailabilityStep({
  availability,
  onAvailabilityChange,
  timezone,
  onTimezoneChange,
  onBack,
  onSubmit,
  cohort,
}: AvailabilityStepProps) {
```

**Step 3: In SignupWizard, find selected cohort and pass it**

In `SignupWizard.tsx`, update the AvailabilityStep usage (around line 235):

```typescript
{currentStep === 3 && (
  <AvailabilityStep
    availability={formData.availability}
    onAvailabilityChange={(data) =>
      setFormData((prev) => ({ ...prev, availability: data }))
    }
    timezone={formData.timezone}
    onTimezoneChange={(tz) =>
      setFormData((prev) => ({ ...prev, timezone: tz }))
    }
    onBack={() => setCurrentStep(2)}
    onSubmit={handleSubmit}
    cohort={availableCohorts.find(c => c.cohort_id === formData.selectedCohortId) ?? null}
  />
)}
```

**Step 4: Commit**

```bash
jj new -m "feat: pass selected cohort to AvailabilityStep"
```

---

## Task 4: Display date range in AvailabilityStep

**Files:**
- Modify: `web_frontend/src/components/signup/AvailabilityStep.tsx:27-35`

**Step 1: Add date formatting helper inside component**

Add this before the return statement:

```typescript
const formatDateRange = () => {
  if (!cohort) return null;

  const startDate = new Date(cohort.cohort_start_date);
  const endDate = new Date(startDate);
  endDate.setDate(endDate.getDate() + cohort.duration_days - 1);

  const formatDate = (date: Date) =>
    date.toLocaleDateString("en-US", { month: "long", day: "numeric" });

  return `${formatDate(startDate)} and ${formatDate(endDate)}`;
};

const dateRange = formatDateRange();
```

**Step 2: Update the description paragraph**

Replace the existing `<p>` element:

```typescript
<p className="text-gray-600 mb-6">
  {dateRange ? (
    <>
      Give us your availability between <strong>{dateRange}</strong>.
      This helps us match you with a group that fits your schedule.
    </>
  ) : (
    <>
      Select the times when you're available to participate in course
      sessions. This helps us match you with a group that fits your schedule.
    </>
  )}
</p>
```

**Step 3: Test manually**

Run: `python main.py --dev --no-bot`
Navigate to signup flow, select a cohort, verify availability step shows date range.

**Step 4: Commit**

```bash
jj new -m "feat: show course date range on availability selector"
```

---

## Summary

4 small tasks:
1. Backend: Add `duration_days` to cohort query
2. Frontend: Update `Cohort` TypeScript type
3. Frontend: Pass selected cohort through SignupWizard
4. Frontend: Display date range in AvailabilityStep
