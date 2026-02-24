"""Agent base class for AgentFlow."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AgentStatus(str, Enum):
    """Agent status."""
    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Agent(ABC):
    """Abstract base class for all AgentFlow agents."""

    name: str
    agent_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    tools: List[Any] = field(default_factory=list)
    memory: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: AgentStatus = AgentStatus.IDLE
    max_iterations: int = 10

    @abstractmethod
    async def run(self, task: Any, context: Dict[str, Any] = None) -> Any:
        """Execute the agent on a given task."""
        ...

    def add_tool(self, tool: Any) -> None:
        """Register a tool with this agent."""
        self.tools.append(tool)

    def set_memory(self, memory: Any) -> None:
        """Attach a memory store to this agent."""
        self.memory = memory

    def to_dict(self) -> Dict[str, Any]:
        """Serialize agent to dict."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "tools_count": len(self.tools),
            "has_memory": self.memory is not None,
            "metadata": self.metadata,
        }

    def __repr__(self) -> str:
        return f"Agent(name={self.name!r}, status={self.status.value}, tools={len(self.tools)})"
