from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "TripStars Task Management"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # MongoDB
    MONGO_URL: str = ""  # Will be loaded from .env as MONGO_URL
    DB_NAME: str = ""

    # Security - JWT
    JWT_SECRET_KEY: str = "tripstars-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # Short-lived access token
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30  # Long-lived refresh token

    # CORS (comma-separated string)
    CORS_ORIGINS: str = "http://localhost:3000"

    # Email Configuration (Phase 4)
    EMAIL_ENABLED: bool = False
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""

    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

    @property
    def MONGODB_URI(self) -> str:
        """Alias for MONGO_URL for backward compatibility"""
        return self.MONGO_URL

    class Config:
        case_sensitive = True
        # Get .env file from backend directory (go up 4 levels from config.py)
        # config.py is at: backend/src/app/core/config.py
        # .env is at: backend/.env
        env_file = str(Path(__file__).parent.parent.parent.parent / ".env")
        extra = "ignore"  # Allow extra fields from environment

settings = Settings()
