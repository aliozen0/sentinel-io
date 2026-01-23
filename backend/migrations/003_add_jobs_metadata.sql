-- Migration: Add metadata column to jobs table
-- Purpose: Store arbitrary JSON data (e.g. analysis results, detailed config)

ALTER TABLE jobs ADD COLUMN metadata TEXT;

-- Verify
PRAGMA table_info(jobs);
