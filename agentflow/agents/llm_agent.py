"""LLM-powered agent implementation for AgentFlow."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from agentflow.agents.base import BaseAgent
from agentflow.core.agent import AgentStatus

logger = logging.getLogger(__name__)


@dataclass
class LLMAgent(BaseAgent):
    """An agent powered by a language model via LiteLLM."""

    model: str = "gpt-4o-mini"
    system_prompt: str = "You are a helpful AI assistant."
    temperature: float = 0.0
    max_tokens: int = 4096
    history: List[Dict[str, str]] = field(default_factory=list)

    async def run(self, task: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute the task using the configured LLM."""
        context = context or {}
        self.status = AgentStatus.RUNNING
        logger.info(f"LLMAgent '{self.name}' running task: {task.name}")

        try:
            import litellm

            messages = [
                {"role": "system", "content": self.system_prompt},
            ]

            # Add conversation history
            messages.extend(self.history)

            # Build user message from task
            user_content = self._build_user_message(task, context)
            messages.append({"role": "user", "content": user_content})

            response = await litellm.acompletion(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            content = response.choices[0].message.content

            # Update history
            self.history.append({"role": "user", "content": user_content})
            self.history.append({"role": "assistant", "content": content})

            self.status = AgentStatus.COMPLETED
            return {
                "result": content,
                "model": self.model,
                "usage": dict(response.usage) if response.usage else {},
            }

        except Exception as e:
            self.status = AgentStatus.FAILED
            logger.error(f"LLMAgent '{self.name}' failed: {e}")
            raise

    def _build_user_message(self, task: Any, context: Dict[str, Any]) -> str:
        """Build the user message from task and context."""
        parts = [f"Task: {task.name}"]
        if task.description:
            parts.append(f"Description: {task.description}")
        if task.input_data:
            parts.append(f"Input: {task.input_data}")
        if context:
            parts.append(f"Context: {context}")
        return "\n".join(parts)

    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.history.clear()
