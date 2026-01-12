-- Migration: Replace reminders_log with notification_log
-- Date: 2026-01-13
-- Description:
--   - Drop unused reminders_log and reminder_recipients_log tables
--   - Drop unused delivery_method and delivery_status enum types
--   - Create new notification_log table for tracking sent notifications

-- =====================================================
-- DROP UNUSED TABLES
-- =====================================================

-- Must drop reminder_recipients_log first (has FK to reminders_log)
DROP TABLE IF EXISTS reminder_recipients_log;
DROP TABLE IF EXISTS reminders_log;

-- =====================================================
-- DROP UNUSED ENUM TYPES
-- =====================================================

DROP TYPE IF EXISTS delivery_method;
DROP TYPE IF EXISTS delivery_status;

-- =====================================================
-- CREATE NOTIFICATION_LOG TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS notification_log (
    log_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    channel_id TEXT,
    message_type TEXT NOT NULL,
    channel TEXT NOT NULL,
    status TEXT NOT NULL,
    error_message TEXT,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_notification_log_user_id ON notification_log(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_log_sent_at ON notification_log(sent_at);

