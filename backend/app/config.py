import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    APP_NAME: str = "Anti-Sarika Control Plane"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # Security & Tokens
    SECRET_KEY: str = Field(
        default="anti-sarika-insecure-dev-secret-key-change-in-production-min-32-chars",
        description="Secret key for JWT token generation and validation"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./anti_sarika.db",
        description="Async SQLAlchemy database URL (SQLite or PostgreSQL)"
    )

    # Replay Protection & Nonce window
    NONCE_EXPIRATION_SECONDS: int = 900  # 15 minutes
    REQUEST_TIMESTAMP_TOLERANCE_SECONDS: int = 300  # 5 minutes clock skew tolerance

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"]

    # Backend Master Cryptographic Key (PEM encoded)
    BACKEND_PRIVATE_KEY_PEM: Optional[str] = None
    BACKEND_PUBLIC_KEY_PEM: Optional[str] = None


settings = Settings()
