"""Runtime configuration for radiquant-v5.

Security-sensitive defaults are development-only. Production deployments must provide
strong secrets and a PostgreSQL DATABASE_URL via environment variables.
"""

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment and optional .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = Field(default="development", alias="ENVIRONMENT")
    database_url: str = Field(
        default="postgresql+asyncpg://radiquant_v5:radiquant_v5_dev@127.0.0.1:5432/radiquant_v5",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://127.0.0.1:6379/5", alias="REDIS_URL")
    secret_key: SecretStr = Field(default=SecretStr("change-me-min-32-chars"), alias="SECRET_KEY")
    access_token_ttl_minutes: int = Field(default=30, alias="ACCESS_TOKEN_TTL_MINUTES", ge=1)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached runtime settings."""
    return Settings()
