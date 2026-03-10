# agentflow/core/config.py
from __future__ import annotations

import os
from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    app_name: str = "AgentFlow Framework"
    app_version: str = "2.0.0"
    debug: bool = False
    log_level: str = "INFO"
    app_env: str = "development"

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # LLM API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    mistral_api_key: Optional[str] = None
    together_api_key: Optional[str] = None
    perplexity_api_key: Optional[str] = None
    fireworks_api_key: Optional[str] = None
    cohere_api_key: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_deployment: Optional[str] = None

    # Default LLM - Grok via Groq
    active_llm_model: str = "groq/llama-3.1-8b-instant"
    llm_temperature: float = 0.0
    llm_max_tokens: int = 4096

    # Memory
    enable_memory: bool = True
    memory_backend: str = "db"  # db | in_memory
    memory_window_size: int = 20  # number of messages to keep in context window

    # Database
    database_url: str = "sqlite:///./agentflow.db"
    sync_database_url: str = "sqlite:///./agentflow.db"

    secret_key: str = "dev-secret-key-change-in-production"
    cors_origins: str = "*"
    human_approval_required: bool = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
