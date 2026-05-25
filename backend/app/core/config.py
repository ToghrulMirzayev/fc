"""Application settings loaded from environment."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Branding / codename — change APP_NAME to rebrand.
    APP_NAME: str = "Fitness Court"
    APP_DOMAIN: str = "fitnesscourt.local"

    # Runtime
    ENV: Literal["dev", "staging", "prod"] = "dev"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    API_PORT: int = 8000

    # Security
    SECRET_KEY: str = Field(..., min_length=32)
    QR_SIGNING_KEY: str = Field(..., min_length=32)
    ACCESS_TOKEN_TTL_MIN: int = 15
    REFRESH_TOKEN_TTL_DAYS: int = 14
    QR_TOKEN_TTL_SECONDS: int = 30

    # Database
    DATABASE_URL: str

    # Redis / Celery
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # Telegram bot
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_SECRET: str = ""
    TELEGRAM_WEBHOOK_URL: str = ""

    # Email
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "noreply@fitnesscourt.local"

    # Sentry
    SENTRY_DSN_BACKEND: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
