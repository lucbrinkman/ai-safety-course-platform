-- Migration: Rename lesson_id to lesson_slug and simplify courses table
-- Date: 2026-01-13
-- Description:
--   - Rename lesson_id to lesson_slug in lesson_sessions table
--   - Rename lesson_id to lesson_slug in content_events table
--   - Simplify courses table to just course_id and course_slug
--   - Rename indexes accordingly

-- =====================================================
-- LESSON_SESSIONS: lesson_id -> lesson_slug
-- =====================================================

ALTER TABLE lesson_sessions RENAME COLUMN lesson_id TO lesson_slug;

-- Rename index
DROP INDEX IF EXISTS idx_lesson_sessions_lesson_id;
CREATE INDEX IF NOT EXISTS idx_lesson_sessions_lesson_slug ON lesson_sessions(lesson_slug);

-- =====================================================
-- CONTENT_EVENTS: lesson_id -> lesson_slug
-- =====================================================

ALTER TABLE content_events RENAME COLUMN lesson_id TO lesson_slug;

-- Rename index
DROP INDEX IF EXISTS idx_content_events_lesson_id;
CREATE INDEX IF NOT EXISTS idx_content_events_lesson_slug ON content_events(lesson_slug);

-- =====================================================
-- COURSES: Simplify to just course_id and course_slug
-- =====================================================

-- Add course_slug column
ALTER TABLE courses ADD COLUMN IF NOT EXISTS course_slug TEXT;

-- Set course_slug from course_name for existing rows (convert to lowercase, replace spaces with dashes)
UPDATE courses SET course_slug = LOWER(REPLACE(course_name, ' ', '-')) WHERE course_slug IS NULL;

-- Make course_slug not null and unique
ALTER TABLE courses ALTER COLUMN course_slug SET NOT NULL;
ALTER TABLE courses ADD CONSTRAINT uq_courses_course_slug UNIQUE (course_slug);

-- Drop unused columns
ALTER TABLE courses DROP COLUMN IF EXISTS course_name;
ALTER TABLE courses DROP COLUMN IF EXISTS description;
ALTER TABLE courses DROP COLUMN IF EXISTS duration_days_options;
ALTER TABLE courses DROP COLUMN IF EXISTS is_public;
ALTER TABLE courses DROP COLUMN IF EXISTS updated_at;
ALTER TABLE courses DROP COLUMN IF EXISTS created_by_user_id;

-- Create index on course_slug
CREATE INDEX IF NOT EXISTS idx_courses_slug ON courses(course_slug);

