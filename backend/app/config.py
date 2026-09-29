"""
Central application configuration.

All values are read from environment variables (or a .env file via
python-dotenv).  Sensitive fields such as database passwords and JWT
secrets are never given hard-coded defaults — the application will
raise a clear error if they are missing.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        # Ignore extra vars present in .env but not declared here.
        extra="ignore",
    )

    # ── Server ────────────────────────────────────────────────────────────────
    backend_host: str = Field(default="0.0.0.0")
    backend_port: int = Field(default=8000)
    debug: bool = Field(default=False)

    # ── Security ──────────────────────────────────────────────────────────────
    jwt_secret: str = Field(
        ...,
        description="Long random string used to sign JWT tokens. Required.",
    )
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=30)

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = Field(
        ...,
        description="PostgreSQL async URL, e.g. postgresql+asyncpg://user:pass@host/db",
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Stored as a comma-separated string in .env, parsed into a list here.
    cors_origins: str = Field(default="http://localhost:5173,http://localhost:3000")

    @property
    def cors_origins_list(self) -> List[str]:
        """Return CORS origins as a Python list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    login_rate_limit: int = Field(
        default=5, description="Max login requests per IP per minute."
    )
    api_rate_limit: int = Field(
        default=60, description="Max general API requests per IP per minute."
    )

    # ── Evidence Storage ──────────────────────────────────────────────────────
    evidence_dir: str = Field(default="evidence")
    evidence_max_size_bytes: int = Field(default=5 * 1024 * 1024)  # 5 MB

    # ── External APIs ─────────────────────────────────────────────────────────
    nominatim_url: str = Field(default="https://nominatim.openstreetmap.org")
    nominatim_user_agent: str = Field(default="SmartParkingPlatform/1.0")
    openrouteservice_api_key: str = Field(default="")
    ai_internal_api_key: str = Field(default="dev-ai-key-local")

    # ── Logging ───────────────────────────────────────────────────────────────
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="logs/app.log")

    # ── AI / CV Thresholds (mirrored here so the backend can read them too) ───
    confidence_threshold: float = Field(default=0.5)
    iou_threshold: float = Field(default=0.45)
    frame_skip: int = Field(default=2)
    violation_duration_seconds: int = Field(default=120)
    parking_overlap_threshold: float = Field(default=0.3)

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if v in ("CHANGE_ME", "CHANGE_ME_USE_A_LONG_RANDOM_STRING", ""):
            raise ValueError(
                "JWT_SECRET must be set to a strong random value. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(48))\""
            )
        if len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long.")
        return v

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if "CHANGE_ME" in v or not v:
            raise ValueError(
                "DATABASE_URL must be set to a valid database connection string."
            )
        # Ensure async driver is used with SQLAlchemy async sessions.
        if v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        # Allow SQLite for local development (no PostgreSQL required)
        if v.startswith("sqlite://"):
            v = v.replace("sqlite://", "sqlite+aiosqlite://", 1)
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the singleton Settings instance.

    Using lru_cache ensures environment variables are parsed once and
    reused across the application.  During testing, call
    get_settings.cache_clear() after patching env vars.
    """
    return Settings()
