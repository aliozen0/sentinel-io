-- Fix Documents FK to reference public.profiles instead of auth.users
-- Reason: We are using Custom Auth (users stored in public.profiles), so FK must reference that.

BEGIN;

-- 1. Drop old constraint
ALTER TABLE public.documents DROP CONSTRAINT IF EXISTS documents_user_id_fkey;

-- 2. Add new constraint referencing public.profiles
ALTER TABLE public.documents
    ADD CONSTRAINT documents_user_id_fkey
    FOREIGN KEY (user_id)
    REFERENCES public.profiles(id)
    ON DELETE CASCADE;

COMMIT;
