"""Unified LLM gateway via LiteLLM with routing and fallback."""
from __future__ import annotations
import asyncio
from typing import Any, Optional
import litellm
from litellm import acompletion
from agentflow.llm.detector import detect_providers, get_active_model
from agentflow.core.config import get_settings
import structlog

logger = structlog.get_logger(__name__)
litellm.drop_params = True


class ModelGateway:
    """Routes LLM calls through LiteLLM with auto-fallback."""

    def __init__(self, model: Optional[str] = None):
        self._settings = get_settings()
        self._primary_model = model or get_active_model()
        self._fallback_chain = self._build_fallback_chain()

    def _build_fallback_chain(self) -> list[str]:
        providers = detect_providers()
        chain = [p.default_model for p in providers]
        chain.append("ollama/llama3")
        seen, result = set(), []
        for m in chain:
            if m not in seen:
                seen.add(m)
                result.append(m)
        return result

    async def achat(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> str:
        target = model or self._primary_model
        attempt_chain = [target] + [m for m in self._fallback_chain if m != target]

        for attempt_model in attempt_chain:
            try:
                logger.info("llm_request", model=attempt_model)
                response = await acompletion(
                    model=attempt_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                content = response.choices[0].message.content
                logger.info("llm_response", model=attempt_model)
                return content
            except Exception as exc:
                logger.warning("llm_fallback", failed_model=attempt_model, error=str(exc))
                continue

        raise RuntimeError(f"All LLM providers failed. Chain: {attempt_chain}")

    def chat(self, messages: list[dict], **kwargs: Any) -> str:
        return asyncio.get_event_loop().run_until_complete(self.achat(messages, **kwargs))

    @property
    def active_model(self) -> str:
        return self._primary_model

    def list_available(self) -> list[str]:
        return self._fallback_chain


_gateway: Optional[ModelGateway] = None


def get_gateway(model: Optional[str] = None) -> ModelGateway:
    global _gateway
    if _gateway is None or model:
        _gateway = ModelGateway(model)
    return _gateway
