from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    APP_ENV: str = "dev"
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_EXPIRES_MIN: int = 30
    JWT_REFRESH_EXPIRES_MIN: int = 43200

    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_BUCKET: str = "math-png"

    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    MAX_UPLOAD_MB: int = 2
    RATE_LIMIT: str = "60/minute"

    class Config:
        env_file = ".env"

    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()