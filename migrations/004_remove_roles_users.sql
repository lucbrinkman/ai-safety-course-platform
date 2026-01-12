-- Migration: Remove roles_users table, add is_admin flag to users
-- Date: 2026-01-12
-- Description: Consolidate admin role tracking from separate roles_users table
--              into a simple is_admin boolean flag on users table.
--              Facilitator status is already tracked via the facilitators table.

-- Step 1: Add is_admin column to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;

-- Step 2: Migrate admin role from roles_users to users.is_admin
UPDATE users
SET is_admin = TRUE
WHERE user_id IN (
    SELECT user_id FROM roles_users WHERE role = 'admin'
);

-- Step 3: Drop roles_users table
DROP TABLE IF EXISTS roles_users;

-- Step 4: Drop user_role enum type (was only used by roles_users)
DROP TYPE IF EXISTS user_role;
