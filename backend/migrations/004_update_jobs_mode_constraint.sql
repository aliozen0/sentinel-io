-- Migration: Update jobs mode constraint to support ANALYSIS
-- Error was: new row for relation "jobs" violates check constraint "jobs_mode_check"

-- 1. Drop existing constraint
ALTER TABLE jobs DROP CONSTRAINT IF EXISTS jobs_mode_check;

-- 2. Add updated constraint
ALTER TABLE jobs ADD CONSTRAINT jobs_mode_check CHECK (mode IN ('SIMULATION', 'LIVE', 'ANALYSIS'));
