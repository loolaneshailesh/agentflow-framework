"""Base agent abstract class for AgentFlow Framework."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from agentflow.llm.gateway import LLMGateway
from agentflow.observability.logger import get_logger

logger = get_logger(__name__)


class BaseAgent(ABC):
    """Abstract base class that all agents must inherit from."""

    def __init__(
        self,
        name: str,
        description: str,
        gateway: Optional[LLMGateway] = None,
    ):
        self.name = name
        self.description = description
        self._gateway = gateway or LLMGateway()
        logger.info("agent_init", agent=name, model=self._gateway.active_model)

    @abstractmethod
    async def run(self, task: str, context: Dict[str, Any] = {}) -> str:
        """Execute the agent on a given task."""
        ...

    def as_tool(self):
        """Register this agent as a LangChain tool for composition."""
        from agentflow.tools.registry import registry
        registry.register_agent_as_tool(self)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, model={self._gateway.active_model!r})"
