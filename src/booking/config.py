from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["debug", "info", "warning", "error"]
Environment = Literal["development", "test", "production"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="forbid",
    )

    port: int = Field(default=8080, ge=1, le=65535)
    log_level: LogLevel = "info"
    environment: Environment = "development"
    app_version: str = "0.0.0-dev"
    database_url: PostgresDsn

    jwt_secret: SecretStr
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 7


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore