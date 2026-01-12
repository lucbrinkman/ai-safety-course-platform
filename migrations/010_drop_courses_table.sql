-- Migration: Drop courses table, use course_slug directly in cohorts
-- Date: 2026-01-13
-- Description:
--   - Add course_slug column to cohorts
--   - Migrate course_id references to course_slug
--   - Drop course_id column and FK from cohorts
--   - Drop courses table entirely
--   - Add course_slug_override to groups (for A/B testing)

-- =====================================================
-- COHORTS: Add course_slug, migrate data, drop course_id
-- =====================================================

-- Add course_slug column
ALTER TABLE cohorts ADD COLUMN IF NOT EXISTS course_slug TEXT;

-- Migrate: copy course_slug from courses table based on course_id
UPDATE cohorts
SET course_slug = courses.course_slug
FROM courses
WHERE cohorts.course_id = courses.course_id;

-- For any cohorts without a matching course, default to 'default'
UPDATE cohorts SET course_slug = 'default' WHERE course_slug IS NULL;

-- Make course_slug NOT NULL
ALTER TABLE cohorts ALTER COLUMN course_slug SET NOT NULL;

-- Drop the old FK constraint and column
ALTER TABLE cohorts DROP CONSTRAINT IF EXISTS fk_cohorts_course_id_courses;
ALTER TABLE cohorts DROP COLUMN IF EXISTS course_id;

-- Drop old index, create new one
DROP INDEX IF EXISTS idx_cohorts_course_id;
CREATE INDEX IF NOT EXISTS idx_cohorts_course_slug ON cohorts(course_slug);

-- =====================================================
-- DROP COURSES TABLE
-- =====================================================

DROP TABLE IF EXISTS courses;

-- Drop the index that was on courses (if it still exists)
DROP INDEX IF EXISTS idx_courses_slug;

-- =====================================================
-- GROUPS: Add course_slug_override for A/B testing
-- =====================================================

-- Add nullable course_slug_override column
-- NULL = use cohort's course_slug, set = override for A/B testing
ALTER TABLE groups ADD COLUMN IF NOT EXISTS course_slug_override TEXT;
