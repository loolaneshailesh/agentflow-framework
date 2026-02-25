# agentflow/core/config.py
from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    app_name: str = "AgentFlow Framework"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None

    database_url: str = "sqlite:///./agentflow.db"

    enable_memory: bool = True
    memory_backend: str = "in_memory"

    secret_key: str = "dev-secret-key-change-in-production"
    human_approval_required: bool = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
