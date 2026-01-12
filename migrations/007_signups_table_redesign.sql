-- Migration: Redesign courses_users table to signups
-- Date: 2026-01-13
-- Description:
--   - Rename courses_users table to signups
--   - Rename courses_users_id to signup_id
--   - Remove course_id (derivable from cohort)
--   - Rename role_in_cohort to role
--   - Remove grouping_status (row exists = awaiting, ungroupable_reason != NULL = ungroupable)
--   - Remove grouping_attempt_count and last_grouping_attempt_at (not needed)
--   - Remove completed_at (moved to groups_users)
--   - Add completed_at to groups_users
--   - Remove dropout_details from groups_users
--   - Change dropout_reason from enum to text
--   - Drop unused enum types

-- =====================================================
-- RENAME courses_users TO signups
-- =====================================================

-- Rename the table
ALTER TABLE courses_users RENAME TO signups;

-- Rename primary key column
ALTER TABLE signups RENAME COLUMN course_user_id TO signup_id;

-- Rename primary key constraint
ALTER TABLE signups RENAME CONSTRAINT pk_courses_users TO pk_signups;

-- Rename indexes
ALTER INDEX IF EXISTS idx_courses_users_user_id RENAME TO idx_signups_user_id;
ALTER INDEX IF EXISTS idx_courses_users_cohort_id RENAME TO idx_signups_cohort_id;

-- =====================================================
-- REMOVE COLUMNS FROM signups
-- =====================================================

ALTER TABLE signups DROP COLUMN IF EXISTS course_id;
ALTER TABLE signups DROP COLUMN IF EXISTS grouping_status;
ALTER TABLE signups DROP COLUMN IF EXISTS grouping_attempt_count;
ALTER TABLE signups DROP COLUMN IF EXISTS last_grouping_attempt_at;
ALTER TABLE signups DROP COLUMN IF EXISTS completed_at;

-- =====================================================
-- RENAME role_in_cohort TO role
-- =====================================================

ALTER TABLE signups RENAME COLUMN role_in_cohort TO role;

-- =====================================================
-- GROUPS_USERS TABLE CHANGES
-- =====================================================

-- Add completed_at column
ALTER TABLE groups_users ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITH TIME ZONE;

-- Remove dropout_details column
ALTER TABLE groups_users DROP COLUMN IF EXISTS dropout_details;

-- Change dropout_reason from enum to text
-- (Must drop and recreate the column to change the type)
ALTER TABLE groups_users DROP COLUMN IF EXISTS dropout_reason;
ALTER TABLE groups_users ADD COLUMN dropout_reason TEXT;

-- =====================================================
-- DROP UNUSED ENUM TYPES
-- =====================================================

-- Drop grouping_status enum type
DROP TYPE IF EXISTS grouping_status;

-- Drop dropout_reason enum type
DROP TYPE IF EXISTS dropout_reason;

