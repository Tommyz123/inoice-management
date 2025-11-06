-- Migration script to add payment-related fields to invoices table
-- This script can be used for both SQLite and PostgreSQL (Supabase)

-- Add payment_status column (default: unpaid)
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS payment_status TEXT DEFAULT 'unpaid' NOT NULL;

-- Add payment_proof_path column (stores path to payment proof PDF)
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS payment_proof_path TEXT;

-- Add payment_date column (stores date when payment was made)
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS payment_date TEXT;

-- For existing records, ensure payment_status is set to 'unpaid' if NULL
UPDATE invoices SET payment_status = 'unpaid' WHERE payment_status IS NULL;
