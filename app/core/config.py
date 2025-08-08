from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    # App settings
    APP_ENV: str = "dev"
    APP_NAME: str = "Math Buddy Backend"
    
    # Database
    DATABASE_URL: str
    
    # JWT settings
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRES_MIN: int = 30
    JWT_REFRESH_EXPIRES_MIN: int = 43200  # 30 days
    
    # Supabase settings
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_BUCKET: str = "homework-questions"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Upload settings
    MAX_UPLOAD_MB: int = 2
    ALLOWED_IMAGE_TYPES: List[str] = ["image/png", "image/jpeg"]
    
    # Rate limiting
    RATE_LIMIT: str = "60/minute"
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if isinstance(self.ALLOWED_ORIGINS, str):
            self.ALLOWED_ORIGINS = [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()
