from __future__ import annotations
import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://agentflow:agentflow@localhost:5432/agentflow"
    sync_database_url: str = "postgresql://agentflow:agentflow@localhost:5432/agentflow"

    # LLM Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    cohere_api_key: Optional[str] = None
    mistral_api_key: Optional[str] = None
    together_api_key: Optional[str] = None
    perplexity_api_key: Optional[str] = None
    fireworks_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_deployment: Optional[str] = None

    # Local
    ollama_base_url: str = "http://localhost:11434"
    vllm_base_url: str = "http://localhost:8000"
    active_llm_model: Optional[str] = None

    # App
    app_env: str = "development"
    log_level: str = "INFO"
    secret_key: str = "change-me"
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
