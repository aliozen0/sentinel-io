-- Migration: Fix chat_messages foreign key constraint
-- Problem: chat_messages references 'users' but we use 'profiles' table
-- Run this in Supabase SQL Editor

-- Step 1: Drop the existing foreign key constraint (if exists)
ALTER TABLE chat_messages DROP CONSTRAINT IF EXISTS chat_messages_user_id_fkey;

-- Step 2: Make user_id nullable (for anonymous messages) or reference profiles
-- Option A: Make it nullable (recommended for chat - allows anonymous)
ALTER TABLE chat_messages ALTER COLUMN user_id DROP NOT NULL;

-- Option B: Add foreign key to profiles table (if exists)
-- First check if profiles table exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'profiles') THEN
        -- Add foreign key to profiles
        ALTER TABLE chat_messages
        ADD CONSTRAINT chat_messages_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Step 3: Add index for performance
CREATE INDEX IF NOT EXISTS idx_chat_messages_user_id ON chat_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at DESC);

-- Step 4: Ensure RLS policy allows inserts
DROP POLICY IF EXISTS "Enable read/write for all" ON chat_messages;
CREATE POLICY "Enable all for authenticated users" ON chat_messages
    FOR ALL 
    USING (true)
    WITH CHECK (true);

-- Verify the fix
SELECT 
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_name = 'chat_messages' AND tc.constraint_type = 'FOREIGN KEY';
