-- Migration: Add active_persona_id to users table
-- Date: 2026-01-04
-- Description: Add active_persona_id column to store user's default persona preference

ALTER TABLE users ADD COLUMN IF NOT EXISTS active_persona_id VARCHAR(255) NULL;

-- Add comment
COMMENT ON COLUMN users.active_persona_id IS 'ID of the persona to use as default in chats';
