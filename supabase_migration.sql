-- Supabase Migration Script
-- Run this in your Supabase SQL Editor to add payment-related fields
-- https://app.supabase.com/project/_/sql

-- Step 1: Add new columns to existing invoices table
ALTER TABLE public.invoices
ADD COLUMN IF NOT EXISTS payment_status TEXT DEFAULT 'unpaid' NOT NULL,
ADD COLUMN IF NOT EXISTS payment_proof_path TEXT,
ADD COLUMN IF NOT EXISTS payment_date TEXT;

-- Step 2: Update existing records to have 'unpaid' status
UPDATE public.invoices
SET payment_status = 'unpaid'
WHERE payment_status IS NULL;

-- Step 3: Verify the changes
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'invoices'
  AND table_schema = 'public'
  AND column_name IN ('payment_status', 'payment_proof_path', 'payment_date')
ORDER BY column_name;

-- Expected output:
-- payment_date        | text | YES | NULL
-- payment_proof_path  | text | YES | NULL
-- payment_status      | text | NO  | 'unpaid'::text
