-- Migration: Schema cleanup - groups and meetings tables
-- Date: 2026-01-12
-- Description:
--   - Add discord_category_id to groups
--   - Remove merge tracking (merged_from_groups, merged_into_group_id)
--   - Remove flags column from groups
--   - Remove rescheduling fields from meetings
--   - Rename scheduled_time_utc to scheduled_at

-- =====================================================
-- GROUPS TABLE CHANGES
-- =====================================================

-- Add discord_category_id column
ALTER TABLE groups ADD COLUMN IF NOT EXISTS discord_category_id TEXT;

-- Remove merge tracking columns
ALTER TABLE groups DROP COLUMN IF EXISTS merged_from_groups;
ALTER TABLE groups DROP COLUMN IF EXISTS merged_into_group_id;

-- Remove flags column
ALTER TABLE groups DROP COLUMN IF EXISTS flags;

-- =====================================================
-- MEETINGS TABLE CHANGES
-- =====================================================

-- Remove rescheduling fields
ALTER TABLE meetings DROP COLUMN IF EXISTS was_rescheduled;
ALTER TABLE meetings DROP COLUMN IF EXISTS reschedule_reason;

-- Rename scheduled_time_utc to scheduled_at
ALTER TABLE meetings RENAME COLUMN scheduled_time_utc TO scheduled_at;

-- Update index name to match new column name
ALTER INDEX IF EXISTS idx_meetings_scheduled_time RENAME TO idx_meetings_scheduled_at;

-- Remove course_id from meetings (course is derivable via cohort)
ALTER TABLE meetings DROP COLUMN IF EXISTS course_id;

-- =====================================================
-- ENUM CHANGES
-- =====================================================

-- Remove 'merged' from group_status enum
-- Note: This requires recreating the enum type in PostgreSQL
-- Only run if no rows use 'merged' status
ALTER TABLE groups ALTER COLUMN status DROP DEFAULT;
ALTER TYPE group_status RENAME TO group_status_old;
CREATE TYPE group_status AS ENUM ('forming', 'active', 'completed', 'cancelled');
ALTER TABLE groups ALTER COLUMN status TYPE group_status USING status::text::group_status;
ALTER TABLE groups ALTER COLUMN status SET DEFAULT 'forming';
DROP TYPE group_status_old;
