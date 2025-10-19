"""
Supabase Storage handler for managing invoice PDF files.

This module provides functions to:
- Upload PDF files to Supabase Storage
- Get public URLs for uploaded files
- Delete files from storage
- Automatically create and configure storage buckets
"""

import io
import os
from datetime import datetime
from typing import Optional, Tuple

import config


class StorageError(Exception):
    """Custom exception for storage operations."""
    pass


def _get_storage_client():
    """Initialize and return Supabase storage client."""
    if not config.SUPABASE_URL or not config.SUPABASE_KEY:
        raise StorageError(
            "Supabase credentials not configured. Please set SUPABASE_URL and SUPABASE_KEY in .env file."
        )

    try:
        from supabase import Client, create_client
    except ImportError as exc:
        raise StorageError(
            "supabase library not installed. Run: pip install supabase"
        ) from exc

    client: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    return client


def init_storage_bucket(bucket_name: str = "invoices") -> Tuple[bool, str]:
    """
    Initialize storage bucket. Creates bucket if it doesn't exist.

    Args:
        bucket_name: Name of the storage bucket (default: "invoices")

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        client = _get_storage_client()

        # List existing buckets
        try:
            buckets = client.storage.list_buckets()
            bucket_exists = any(b.get('name') == bucket_name for b in buckets)

            if bucket_exists:
                return True, f"Bucket '{bucket_name}' already exists."
        except Exception:
            # If listing fails, we'll try to create anyway
            pass

        # Try to create bucket
        try:
            client.storage.create_bucket(
                bucket_name,
                options={
                    "public": True,  # Allow public read access
                    "file_size_limit": 10485760,  # 10MB limit
                    "allowed_mime_types": ["application/pdf"]
                }
            )
            return True, f"Bucket '{bucket_name}' created successfully."
        except Exception as e:
            error_msg = str(e).lower()
            if "already exists" in error_msg or "duplicate" in error_msg:
                return True, f"Bucket '{bucket_name}' already exists."
            raise

    except Exception as e:
        return False, f"Failed to initialize bucket: {str(e)}"


def upload_file(file_data: bytes, original_filename: str, bucket_name: str = "invoices") -> Tuple[Optional[str], Optional[str]]:
    """
    Upload a file to Supabase Storage.

    Args:
        file_data: File content as bytes
        original_filename: Original filename
        bucket_name: Storage bucket name (default: "invoices")

    Returns:
        Tuple of (storage_path: str or None, error_message: str or None)

    Examples:
        >>> with open("invoice.pdf", "rb") as f:
        ...     path, error = upload_file(f.read(), "invoice.pdf")
        >>> if error:
        ...     print(f"Upload failed: {error}")
        ... else:
        ...     print(f"Uploaded to: {path}")
    """
    try:
        client = _get_storage_client()

        # Generate unique filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        # Sanitize filename (remove special characters)
        safe_filename = "".join(c for c in original_filename if c.isalnum() or c in ".-_")
        storage_path = f"{timestamp}_{safe_filename}"

        # Upload file (pass bytes directly)
        response = client.storage.from_(bucket_name).upload(
            path=storage_path,
            file=file_data,
            file_options={
                "content-type": "application/pdf",
                "cache-control": "3600",
                "upsert": "false"
            }
        )

        # Check for errors in response
        if hasattr(response, 'error') and response.error:
            return None, f"Upload failed: {response.error}"

        # Verify upload by checking if we can get the public URL
        verify_url = client.storage.from_(bucket_name).get_public_url(storage_path)
        if not verify_url:
            return None, "Upload succeeded but failed to generate public URL"

        return storage_path, None

    except Exception as e:
        error_msg = str(e)

        # Handle common errors
        if "404" in error_msg or "not found" in error_msg.lower():
            return None, f"Bucket '{bucket_name}' does not exist. Please create it in Supabase Dashboard or run init_storage_bucket()."
        elif "403" in error_msg or "unauthorized" in error_msg.lower():
            return None, "Upload permission denied. Please check your RLS policies in Supabase Dashboard."
        elif "413" in error_msg or "too large" in error_msg.lower():
            return None, "File size exceeds 10MB limit."
        else:
            return None, f"Upload error: {error_msg}"


def get_public_url(storage_path: str, bucket_name: str = "invoices") -> Optional[str]:
    """
    Get public URL for a file in storage.

    Args:
        storage_path: Path to file in storage (e.g., "20251018_invoice.pdf")
        bucket_name: Storage bucket name (default: "invoices")

    Returns:
        Public URL string or None if error occurs
    """
    try:
        client = _get_storage_client()

        # Get public URL
        url = client.storage.from_(bucket_name).get_public_url(storage_path)

        if not url:
            return None

        return url

    except Exception as e:
        print(f"Error getting public URL: {e}")
        return None


def delete_file(storage_path: str, bucket_name: str = "invoices") -> Tuple[bool, Optional[str]]:
    """
    Delete a file from storage.

    Args:
        storage_path: Path to file in storage
        bucket_name: Storage bucket name (default: "invoices")

    Returns:
        Tuple of (success: bool, error_message: str or None)
    """
    try:
        client = _get_storage_client()

        response = client.storage.from_(bucket_name).remove([storage_path])

        # Check for errors
        if hasattr(response, 'error') and response.error:
            return False, f"Delete failed: {response.error}"

        return True, None

    except Exception as e:
        return False, f"Delete error: {str(e)}"


def test_connection() -> Tuple[bool, str]:
    """
    Test Supabase Storage connection.

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        client = _get_storage_client()
        buckets = client.storage.list_buckets()
        return True, f"Connection successful. Found {len(buckets)} bucket(s)."
    except Exception as e:
        return False, f"Connection failed: {str(e)}"


# Determine whether to use Supabase Storage based on environment
def should_use_storage() -> bool:
    """
    Check if Supabase Storage should be used.

    Returns:
        True if USE_SUPABASE_STORAGE is enabled and credentials are available
    """
    use_storage = os.getenv("USE_SUPABASE_STORAGE", "").strip().lower() in ("true", "1", "yes")
    has_credentials = bool(config.SUPABASE_URL and config.SUPABASE_KEY)
    return use_storage and has_credentials
