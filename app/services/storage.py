import io
from typing import Tuple
from supabase import create_client, Client
from ..core.config import get_settings

settings = get_settings()
_supabase: Client | None = None

def supabase_client() -> Client:
    global _supabase
    if _supabase is None:
        _supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    return _supabase


def upload_png(file_bytes: bytes, object_key: str) -> Tuple[bool, str]:
    """Uploads a PNG to Supabase Storage (private bucket). Returns (ok, path)."""
    sb = supabase_client()
    # content_type inferred by Supabase; we pass file-like
    resp = sb.storage.from_(settings.SUPABASE_BUCKET).upload(object_key, file_bytes, file_options={"content-type": "image/png", "upsert": True})
    if resp is None or getattr(resp, "error", None):
        return False, str(getattr(resp, "error", "upload_failed"))
    # path is usually object_key; store and use it as image_key
    return True, object_key