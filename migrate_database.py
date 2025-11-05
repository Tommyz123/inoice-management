#!/usr/bin/env python3
"""
Database migration script to add payment-related fields.
Run this script to update your existing database with new payment fields.
"""

import os
import sys
from pathlib import Path

def migrate_sqlite():
    """Migrate SQLite database"""
    import sqlite3

    db_path = Path(__file__).resolve().parent / 'invoices.db'

    if not db_path.exists():
        print(f"SQLite database not found at {db_path}")
        print("No migration needed - new fields will be created automatically.")
        return True

    print(f"Migrating SQLite database at {db_path}...")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if columns already exist
        cursor.execute("PRAGMA table_info(invoices)")
        columns = [col[1] for col in cursor.fetchall()]

        migrations_needed = []
        if 'payment_status' not in columns:
            migrations_needed.append(("payment_status", "ALTER TABLE invoices ADD COLUMN payment_status TEXT DEFAULT 'unpaid' NOT NULL"))
        if 'payment_proof_path' not in columns:
            migrations_needed.append(("payment_proof_path", "ALTER TABLE invoices ADD COLUMN payment_proof_path TEXT"))
        if 'payment_date' not in columns:
            migrations_needed.append(("payment_date", "ALTER TABLE invoices ADD COLUMN payment_date TEXT"))

        if not migrations_needed:
            print("✓ All payment fields already exist in SQLite database")
            return True

        # Execute migrations
        for field_name, sql in migrations_needed:
            print(f"  Adding column: {field_name}")
            cursor.execute(sql)

        # Update existing records
        cursor.execute("UPDATE invoices SET payment_status = 'unpaid' WHERE payment_status IS NULL")

        conn.commit()
        conn.close()

        print("✓ SQLite database migration completed successfully")
        return True

    except Exception as e:
        print(f"✗ Error migrating SQLite database: {e}")
        return False


def migrate_supabase():
    """Migrate Supabase/PostgreSQL database"""
    try:
        import psycopg
        from urllib.parse import urlparse
        import config
    except ImportError as e:
        print(f"✗ Required dependencies not found: {e}")
        print("Install with: pip install psycopg")
        return False

    password = os.getenv("SUPABASE_DB_PASSWORD")
    if not password:
        print("⚠ SUPABASE_DB_PASSWORD not set. Skipping Supabase migration.")
        print("If you're using Supabase, please set this variable and run migration again.")
        return True

    if not config.SUPABASE_URL:
        print("⚠ SUPABASE_URL not configured. Skipping Supabase migration.")
        return True

    print("Migrating Supabase/PostgreSQL database...")

    try:
        parsed = urlparse(config.SUPABASE_URL)
        host_ref = parsed.netloc.split(".")[0] if parsed.netloc else ""
        host = f"db.{host_ref}.supabase.co"

        connection_kwargs = {
            "dbname": os.getenv("SUPABASE_DB_NAME", "postgres"),
            "user": os.getenv("SUPABASE_DB_USER", "postgres"),
            "password": password,
            "host": os.getenv("SUPABASE_DB_HOST", host),
            "port": int(os.getenv("SUPABASE_DB_PORT", "5432")),
            "sslmode": os.getenv("SUPABASE_DB_SSLMODE", "require"),
        }

        with psycopg.connect(**connection_kwargs) as conn:
            # Check if columns exist
            cursor = conn.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'invoices' AND table_schema = 'public'
            """)
            columns = [row[0] for row in cursor.fetchall()]

            migrations_needed = []
            if 'payment_status' not in columns:
                migrations_needed.append(("payment_status", "ALTER TABLE invoices ADD COLUMN payment_status TEXT DEFAULT 'unpaid' NOT NULL"))
            if 'payment_proof_path' not in columns:
                migrations_needed.append(("payment_proof_path", "ALTER TABLE invoices ADD COLUMN payment_proof_path TEXT"))
            if 'payment_date' not in columns:
                migrations_needed.append(("payment_date", "ALTER TABLE invoices ADD COLUMN payment_date TEXT"))

            if not migrations_needed:
                print("✓ All payment fields already exist in Supabase database")
                return True

            # Execute migrations
            for field_name, sql in migrations_needed:
                print(f"  Adding column: {field_name}")
                conn.execute(sql)

            # Update existing records
            conn.execute("UPDATE invoices SET payment_status = 'unpaid' WHERE payment_status IS NULL")

            conn.commit()

        print("✓ Supabase database migration completed successfully")
        return True

    except Exception as e:
        print(f"✗ Error migrating Supabase database: {e}")
        return False


def main():
    print("=" * 60)
    print("Invoice Management System - Database Migration")
    print("Adding payment-related fields")
    print("=" * 60)
    print()

    backend = os.getenv("DATA_BACKEND", "").strip().lower()

    if backend == "supabase":
        success = migrate_supabase()
    elif backend == "sqlite":
        success = migrate_sqlite()
    else:
        # Auto-detect
        print("Auto-detecting database backend...")
        sqlite_success = migrate_sqlite()
        supabase_success = migrate_supabase()
        success = sqlite_success or supabase_success

    print()
    if success:
        print("=" * 60)
        print("✓ Migration completed successfully!")
        print("=" * 60)
        return 0
    else:
        print("=" * 60)
        print("✗ Migration failed. Please check the errors above.")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
