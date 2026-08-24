"""Application configuration."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = REPO_ROOT / "data"

TENANT_ID = "northstar"
CUSTOMER_ID = "alex"
DEMO_AS_OF = datetime(2026, 8, 1, 12, 0, 0, tzinfo=UTC)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    openai_timeout_seconds: float = 60.0

    demo_api_host: str = "127.0.0.1"
    demo_api_port: int = 8000
    cors_origin: str = "http://localhost:3000"

    cogkura_memory_budget_tokens: int = Field(default=750, alias="COGKURA_MEMORY_BUDGET_TOKENS")
    max_message_length: int = 2000

    data_dir: Path = DATA_DIR

    @property
    def model_available(self) -> bool:
        return bool(self.openai_api_key and self.openai_api_key.strip())


def get_settings() -> Settings:
    return Settings()
