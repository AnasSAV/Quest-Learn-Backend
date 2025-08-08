from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
import jwt
from typing import Optional, Dict, Any
from .config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_token(sub: str, role: str, expires_min: int | None = None, extra: Optional[Dict[str, Any]] = None) -> str:
    exp_min = expires_min or settings.JWT_EXPIRES_MIN
    now = datetime.now(timezone.utc)
    payload = {"sub": sub, "role": role, "iat": int(now.timestamp()), "exp": int((now + timedelta(minutes=exp_min)).timestamp())}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])