-- Migration: Fix jobs table ID type
-- Problem: id is UUID but application uses custom string format (e.g. exec_...)
-- Run this in Supabase SQL Editor

-- Change id column type to TEXT to support "exec_..." format
ALTER TABLE jobs ALTER COLUMN id TYPE TEXT;

-- Verify
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'jobs' AND column_name = 'id';
