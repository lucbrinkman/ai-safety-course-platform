-- migrations/003_nullable_session_user_id.sql
-- Allow anonymous lesson sessions (user_id can be NULL until claimed)

ALTER TABLE lesson_sessions
ALTER COLUMN user_id DROP NOT NULL;

-- Add index for finding unclaimed sessions
CREATE INDEX idx_lesson_sessions_unclaimed
ON lesson_sessions (session_id)
WHERE user_id IS NULL;
