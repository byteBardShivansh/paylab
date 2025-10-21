"""
Centralized configuration management using Pydantic BaseSettings.

This module consolidates all environment variable access into a single Settings class,
following the 12-factor app configuration pattern.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env file.
    
    This class consolidates all environment variable access across the application.
    All configuration should be accessed through this class rather than direct
    os.environ or os.getenv calls.
    """
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "payments-service"
    ENV: str = Field(default="development", description="Environment name: development/staging/production")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    API_KEY: str = Field(default="dev-secret", description="API key required in X-API-KEY header")

    # Default to local SQLite file for quick start; override with Postgres in production
    DATABASE_URL: str = Field(
        default="sqlite+pysqlite:///./payments.db",
        description="SQLAlchemy DB URL. e.g., postgresql+psycopg://user:pass@host:5432/dbname",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Returns:
        Settings: The application configuration instance
    """
    return Settings()  # type: ignore[call-arg]
