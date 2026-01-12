-- Migration: Remove unused fields and rename dropout_reason
-- Date: 2026-01-13
-- Description:
--   - Remove average_rating and rating_count from facilitators
--   - Remove notes and recurrence_pattern from groups
--   - Rename dropout_reason to reason_for_leaving in groups_users

-- =====================================================
-- FACILITATORS: Remove rating fields
-- =====================================================

ALTER TABLE facilitators DROP COLUMN IF EXISTS average_rating;
ALTER TABLE facilitators DROP COLUMN IF EXISTS rating_count;

-- =====================================================
-- GROUPS: Remove unused fields
-- =====================================================

ALTER TABLE groups DROP COLUMN IF EXISTS notes;
ALTER TABLE groups DROP COLUMN IF EXISTS recurrence_pattern;

-- =====================================================
-- GROUPS_USERS: Rename dropout_reason to reason_for_leaving
-- =====================================================

ALTER TABLE groups_users RENAME COLUMN dropout_reason TO reason_for_leaving;
