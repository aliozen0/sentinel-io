-- Fix Foreign Key Constraint on jobs table
-- The issue is that 'jobs.user_id' references 'auth.users' which prevents local/hybrid users from creating jobs.
-- We must change it to reference 'public.profiles' which is our hybrid user table.

BEGIN;

-- 1. Drop the existing strict constraint
ALTER TABLE jobs DROP CONSTRAINT IF EXISTS jobs_user_id_fkey;

-- 2. Add the new constraint referencing profiles
ALTER TABLE jobs 
    ADD CONSTRAINT jobs_user_id_fkey 
    FOREIGN KEY (user_id) 
    REFERENCES public.profiles(id)
    ON DELETE CASCADE;

COMMIT;
