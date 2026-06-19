"""
Supabase Storage wrapper for resume files.

All file I/O with Supabase Storage goes through this module.
The rest of the app never imports the supabase client directly.

Bucket layout:
  {user_id}/{resume_id}/{original_filename}

Example:
  a1b2c3d4-…/d4e5f6a7-…/my_resume.pdf
"""

import logging
from decouple import config
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy client — created once, reused for all requests in the process
# ---------------------------------------------------------------------------
_client: Client | None = None


def _get_client() -> Client:
    """Return (and lazily initialise) the Supabase client."""
    global _client
    if _client is None:
        url = config('SUPABASE_URL')
        key = config('SUPABASE_SERVICE_KEY')
        _client = create_client(url, key)
    return _client


def _bucket() -> str:
    """Return the configured bucket name."""
    return config('SUPABASE_BUCKET_NAME', default='resumes')


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def upload(user_id: str, resume_id: str, filename: str, file_bytes: bytes) -> str:
    """
    Upload a resume file to Supabase Storage.

    Returns the storage_path string that should be saved on ResumeRecord.
    Raises StorageError on failure.
    """
    path = f"{user_id}/{resume_id}/{filename}"
    try:
        _get_client().storage.from_(_bucket()).upload(
            path=path,
            file=file_bytes,
            file_options={"content-type": "application/pdf"},
        )
        logger.info("Uploaded resume to storage path: %s", path)
        return path
    except Exception as exc:
        logger.exception("Storage upload failed for path %s", path)
        raise StorageError(f"Failed to upload file: {exc}") from exc


def download(storage_path: str) -> bytes:
    """
    Download a resume file from Supabase Storage.

    Returns the raw file bytes.
    Raises StorageError on failure.
    """
    try:
        data = _get_client().storage.from_(_bucket()).download(storage_path)
        return data
    except Exception as exc:
        logger.exception("Storage download failed for path %s", storage_path)
        raise StorageError(f"Failed to download file: {exc}") from exc


def delete(storage_path: str) -> None:
    """
    Delete a resume file from Supabase Storage.

    Raises StorageError on failure — the caller (delete view) must NOT
    remove the DB row if this raises, so the record stays consistent.
    """
    try:
        _get_client().storage.from_(_bucket()).remove([storage_path])
        logger.info("Deleted resume from storage path: %s", storage_path)
    except Exception as exc:
        logger.exception("Storage delete failed for path %s", storage_path)
        raise StorageError(f"Failed to delete file: {exc}") from exc


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class StorageError(Exception):
    """Raised when any Supabase Storage operation fails."""
    pass
