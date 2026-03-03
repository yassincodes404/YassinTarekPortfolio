"""Application configuration loaded from environment variables."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Portfolio"
    SECRET_KEY: str = "change-me-to-a-random-string"
    DEBUG: bool = False

    # Database
    DATA_DIR: str = "./data"
    DATABASE_URL: str = ""  # auto-built from DATA_DIR if empty

    # Uploads
    UPLOAD_DIR: str = "./data/uploads"
    MAX_IMAGE_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_VIDEO_SIZE: int = 200 * 1024 * 1024  # 200MB
    ALLOWED_IMAGE_TYPES: list[str] = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    ALLOWED_VIDEO_TYPES: list[str] = ["video/mp4", "video/webm"]

    # Admin seed
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_PASSWORD: str = "ChangeMe123!"

    # Sentry (optional)
    SENTRY_DSN: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def database_url_resolved(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        db_path = Path(self.DATA_DIR) / "data.db"
        return f"sqlite+aiosqlite:///{db_path}"

    @property
    def upload_path(self) -> Path:
        p = Path(self.UPLOAD_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def data_path(self) -> Path:
        p = Path(self.DATA_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
