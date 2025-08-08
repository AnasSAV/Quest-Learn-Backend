from typing import Tuple, Optional
from supabase import create_client, Client
from ..core.config import get_settings

settings = get_settings()
_sb: Client | None = None

def supabase_client() -> Client:
    global _sb
    if _sb is None:
        _sb = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    return _sb

def upload_png(file_bytes: bytes, object_key: str) -> tuple[bool, str]:
    sb = supabase_client()
    resp = sb.storage.from_(settings.SUPABASE_BUCKET).upload(
        object_key,
        file_bytes,
        file_options={
            "contentType": "image/png",  # camelCase
            "upsert": "true",            # <-- must be string, not bool
        },
    )

    if isinstance(resp, dict):
        if resp.get("error"):
            err = resp["error"]
            return False, str(getattr(err, "message", err))
        path = resp.get("path") or resp.get("fullPath") or object_key
        return True, path

    data = getattr(resp, "data", None)
    err = getattr(resp, "error", None)
    if err:
        return False, str(getattr(err, "message", err))
    if data:
        path = data.get("path") or data.get("fullPath") or object_key
        return True, path

    return True, object_key

def public_url(key: str) -> Optional[str]:
    """
    Return a public URL if the bucket/object is public; else None.
    """
    sb = supabase_client()
    out = sb.storage.from_(settings.SUPABASE_BUCKET).get_public_url(key)
    # v2 shape: {"data": {"publicUrl": "..."}, "error": None}
    if isinstance(out, dict):
        data = out.get("data") or {}
        return data.get("publicUrl")
    data = getattr(out, "data", None)
    if isinstance(data, dict):
        return data.get("publicUrl")
    return None

def signed_url(key: str, expires_sec: int = 3600) -> Optional[str]:
    """
    Create a temporary signed URL for private buckets.
    """
    sb = supabase_client()
    out = sb.storage.from_(settings.SUPABASE_BUCKET).create_signed_url(key, expires_sec)
    # v2 shape: {"data": {"signedUrl": "..."}, "error": None}
    if isinstance(out, dict):
        data = out.get("data") or {}
        return data.get("signedUrl")
    data = getattr(out, "data", None)
    if isinstance(data, dict):
        return data.get("signedUrl")
    return None

def delete_image(key: str) -> tuple[bool, str]:
    """
    Deletes a file from Supabase Storage.
    Returns (ok, message).
    """
    sb = supabase_client()
    resp = sb.storage.from_(settings.SUPABASE_BUCKET).remove([key])

    if isinstance(resp, dict):
        if resp.get("error"):
            err = resp["error"]
            return False, str(getattr(err, "message", err))
        return True, "deleted"

    err = getattr(resp, "error", None)
    if err:
        return False, str(getattr(err, "message", err))
    return True, "deleted"
