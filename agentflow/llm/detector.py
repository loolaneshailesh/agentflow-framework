"""Auto-detect LLM provider from API key prefix and env vars."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from agentflow.core.config import get_settings


@dataclass
class DetectedProvider:
    provider: str
    default_model: str
    api_key: str
    priority: int


PROVIDER_REGISTRY = [
    ("openai_api_key",     lambda k: k.startswith("sk-") and "ant" not in k,
     "openai",       "gpt-4o",                                          1),
    ("anthropic_api_key",  lambda k: k.startswith("sk-ant-"),
     "anthropic",    "claude-3-5-sonnet-20241022",                       2),
    ("gemini_api_key",     lambda k: k.startswith("AIza"),
     "gemini",       "gemini/gemini-1.5-pro",                            3),
    ("groq_api_key",       lambda k: k.startswith("gsk_"),
     "groq",         "groq/llama-3.1-70b-versatile",                    4),
    ("mistral_api_key",    lambda k: len(k) > 10,
     "mistral",      "mistral/mistral-large-latest",                     5),
    ("cohere_api_key",     lambda k: len(k) > 10,
     "cohere",       "command-r-plus",                                   6),
    ("together_api_key",   lambda k: len(k) > 10,
     "together_ai",  "together_ai/meta-llama/Llama-3-70b-chat-hf",      7),
    ("perplexity_api_key", lambda k: k.startswith("pplx-"),
     "perplexity",   "perplexity/llama-3.1-sonar-large-128k-online",     8),
    ("fireworks_api_key",  lambda k: k.startswith("fw_"),
     "fireworks_ai", "fireworks_ai/accounts/fireworks/models/llama-v3p1-70b-instruct", 9),
    ("deepseek_api_key",   lambda k: len(k) > 10,
     "deepseek",     "deepseek/deepseek-chat",                          10),
    ("azure_openai_api_key", lambda k: len(k) > 10,
     "azure",        "azure/gpt-4o",                                    11),
]


def detect_providers() -> list[DetectedProvider]:
    """Return all configured providers sorted by priority."""
    settings = get_settings()
    detected: list[DetectedProvider] = []
    for attr, check_fn, provider, default_model, priority in PROVIDER_REGISTRY:
        key = getattr(settings, attr, None)
        if key and check_fn(key):
            detected.append(DetectedProvider(
                provider=provider,
                default_model=default_model,
                api_key=key,
                priority=priority,
            ))
    return sorted(detected, key=lambda p: p.priority)


def get_best_provider() -> Optional[DetectedProvider]:
    providers = detect_providers()
    return providers[0] if providers else None


def get_active_model() -> str:
    """Return explicit model from env or best-detected default."""
    settings = get_settings()
    if settings.active_llm_model:
        return settings.active_llm_model
    provider = get_best_provider()
    if provider:
        return provider.default_model
    return "ollama/llama3"
