"""
BizPilot AI - Application Configuration
Reads all settings from environment variables / .env file using Pydantic Settings.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------ #
    # Application
    # ------------------------------------------------------------------ #
    app_name: str = "BizPilot AI"
    app_env: str = "development"
    secret_key: str = "change-me-in-production-must-be-at-least-32-chars!!"
    debug: bool = False
    log_level: str = "INFO"

    # ------------------------------------------------------------------ #
    # Database
    # ------------------------------------------------------------------ #
    database_url: str = "sqlite:///./bizpilot.db"
    database_url_sqlite: str = "sqlite:///./bizpilot.db"

    # ------------------------------------------------------------------ #
    # Groq / LLM
    # ------------------------------------------------------------------ #
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_max_tokens: int = 4096
    groq_temperature: float = 0.3

    # ------------------------------------------------------------------ #
    # Research / Web Search
    # ------------------------------------------------------------------ #
    research_provider: str = "mock"
    research_api_key: str = ""
    serpapi_key: str = ""

    # ------------------------------------------------------------------ #
    # SMTP / Email
    # ------------------------------------------------------------------ #
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_use_tls: bool = True

    # ------------------------------------------------------------------ #
    # URLs & CORS
    # ------------------------------------------------------------------ #
    frontend_url: str = "http://localhost:8501"
    backend_url: str = "http://localhost:8000"
    cors_origins: str = "http://localhost:8501,http://localhost:3000"

    # ------------------------------------------------------------------ #
    # Security / Rate limiting
    # ------------------------------------------------------------------ #
    api_rate_limit: int = 100
    jwt_expire_minutes: int = 1440  # 24 hours

    # ------------------------------------------------------------------ #
    # Feature flags
    # ------------------------------------------------------------------ #
    demo_mode: bool = True

    # ------------------------------------------------------------------ #
    # Validators
    # ------------------------------------------------------------------ #
    @field_validator("secret_key")
    @classmethod
    def secret_key_must_be_long_enough(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters long. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return v

    @field_validator("groq_temperature")
    @classmethod
    def temperature_in_range(cls, v: float) -> float:
        if not (0.0 <= v <= 2.0):
            raise ValueError("GROQ_TEMPERATURE must be between 0.0 and 2.0")
        return v

    # ------------------------------------------------------------------ #
    # Computed properties
    # ------------------------------------------------------------------ #
    @computed_field  # type: ignore[misc]
    @property
    def is_demo_mode(self) -> bool:
        """True when the app is running in demo / showcase mode."""
        return self.demo_mode

    @computed_field  # type: ignore[misc]
    @property
    def cors_origins_list(self) -> List[str]:
        """Return CORS origins as a list of stripped strings."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @computed_field  # type: ignore[misc]
    @property
    def is_production(self) -> bool:
        """True when APP_ENV is 'production'."""
        return self.app_env.lower() == "production"

    @computed_field  # type: ignore[misc]
    @property
    def is_sqlite(self) -> bool:
        """True when the active DATABASE_URL points to SQLite."""
        return self.database_url.startswith("sqlite")

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def get_database_url(self, async_driver: bool = False) -> str:
        """
        Return the database URL, optionally converting to an async driver.

        For SQLite: sqlite:/// -> sqlite+aiosqlite:///
        For PostgreSQL: postgresql:// -> postgresql+asyncpg://
        """
        url = self.database_url
        if async_driver:
            if url.startswith("sqlite:///"):
                url = url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
            elif url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return a cached singleton instance of Settings.

    Usage::

        from app.config import get_settings
        settings = get_settings()
    """
    return Settings()
