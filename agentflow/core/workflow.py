"""Workflow definition and management for AgentFlow."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class Workflow:
    """Represents a workflow definition with tasks and agents."""

    name: str
    description: str = ""
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tasks: List[Any] = field(default_factory=list)
    agents: List[Any] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: WorkflowStatus = WorkflowStatus.PENDING
    max_retries: int = 3
    timeout_seconds: int = 300

    def add_task(self, task: Any) -> None:
        """Add a task to the workflow."""
        self.tasks.append(task)

    def add_agent(self, agent: Any) -> None:
        """Add an agent to the workflow."""
        self.agents.append(agent)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize workflow to dict."""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "tasks_count": len(self.tasks),
            "agents_count": len(self.agents),
            "metadata": self.metadata,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Workflow":
        """Deserialize workflow from dict."""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            workflow_id=data.get("workflow_id", str(uuid.uuid4())),
            metadata=data.get("metadata", {}),
            max_retries=data.get("max_retries", 3),
            timeout_seconds=data.get("timeout_seconds", 300),
        )

    def __repr__(self) -> str:
        return f"Workflow(name={self.name!r}, status={self.status.value}, tasks={len(self.tasks)})"
