"""Task definition for AgentFlow workflow execution."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING_APPROVAL = "waiting_approval"


class TaskPriority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Task:
    """Represents a single unit of work in a workflow."""

    name: str
    description: str = ""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: Optional[str] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Optional[Dict[str, Any]] = None
    dependencies: List[str] = field(default_factory=list)  # list of task_ids
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    requires_approval: bool = False
    max_retries: int = 3
    retry_count: int = 0
    timeout_seconds: int = 60
    metadata: Dict[str, Any] = field(default_factory=dict)
    on_success: Optional[Callable] = None
    on_failure: Optional[Callable] = None
    error: Optional[str] = None

    def is_ready(self, completed_task_ids: List[str]) -> bool:
        """Check if all dependencies are completed."""
        return all(dep in completed_task_ids for dep in self.dependencies)

    def can_retry(self) -> bool:
        """Check if this task can be retried."""
        return self.retry_count < self.max_retries

    def mark_running(self) -> None:
        """Mark task as running."""
        self.status = TaskStatus.RUNNING

    def mark_completed(self, output: Dict[str, Any]) -> None:
        """Mark task as completed with output."""
        self.status = TaskStatus.COMPLETED
        self.output_data = output

    def mark_failed(self, error: str) -> None:
        """Mark task as failed with error message."""
        self.status = TaskStatus.FAILED
        self.error = error
        self.retry_count += 1

    def to_dict(self) -> Dict[str, Any]:
        """Serialize task to dict."""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "agent_id": self.agent_id,
            "status": self.status.value,
            "priority": self.priority.value,
            "requires_approval": self.requires_approval,
            "dependencies": self.dependencies,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "error": self.error,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }

    def __repr__(self) -> str:
        return f"Task(name={self.name!r}, status={self.status.value}, priority={self.priority.value})"
