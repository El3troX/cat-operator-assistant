from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    """Runtime configuration, read from environment variables or backend/.env."""

    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = f"sqlite:///{(BACKEND_DIR / 'cat_assistant.db').as_posix()}"

    # Comma-separated exact origins, e.g. a deployed frontend URL.
    cors_origins: str = ""
    # Default admits any localhost port so Vite falling back to 5174 still works; set empty to disable.
    cors_origin_regex: str = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_json: bool = False

    @field_validator("log_level", mode="before")
    @classmethod
    def _upper_log_level(cls, value: str) -> str:
        return value.upper() if isinstance(value, str) else value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
