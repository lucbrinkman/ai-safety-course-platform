-- Migration: Remove unused fields from users, courses, groups
-- Date: 2026-01-12
-- Description:
--   - Remove unused user fields (reminder, privacy, notes, source)
--   - Remove courses.last_updated_at (redundant with updated_at)
--   - Remove groups.created_by_user_id (groups created by system)

-- =====================================================
-- USERS TABLE - Remove unused fields
-- =====================================================

ALTER TABLE users DROP COLUMN IF EXISTS reminder_preferences;
ALTER TABLE users DROP COLUMN IF EXISTS reminder_timing;
ALTER TABLE users DROP COLUMN IF EXISTS data_sharing_consent;
ALTER TABLE users DROP COLUMN IF EXISTS analytics_opt_in;
ALTER TABLE users DROP COLUMN IF EXISTS public_profile_visible;
ALTER TABLE users DROP COLUMN IF EXISTS show_in_alumni_directory;
ALTER TABLE users DROP COLUMN IF EXISTS notes;
ALTER TABLE users DROP COLUMN IF EXISTS source;

-- =====================================================
-- COURSES TABLE - Remove redundant field
-- =====================================================

ALTER TABLE courses DROP COLUMN IF EXISTS last_updated_at;

-- =====================================================
-- GROUPS TABLE - Remove unused fields
-- =====================================================

ALTER TABLE groups DROP COLUMN IF EXISTS created_by_user_id;
ALTER TABLE groups DROP COLUMN IF EXISTS total_messages_in_channel;
ALTER TABLE groups DROP COLUMN IF EXISTS last_message_at;
ALTER TABLE groups DROP COLUMN IF EXISTS max_capacity;
ALTER TABLE groups DROP COLUMN IF EXISTS min_size_threshold;

-- =====================================================
-- COURSES_USERS TABLE - Remove unused field
-- =====================================================

ALTER TABLE courses_users DROP COLUMN IF EXISTS is_course_committee_member;
