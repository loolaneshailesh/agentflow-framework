# agentflow/core/state.py
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class WorkflowState:
    """Holds runtime state for a workflow execution."""

    def __init__(self, workflow_id: Optional[str] = None):
        self.workflow_id: str = workflow_id or str(uuid.uuid4())
        self.status: WorkflowStatus = WorkflowStatus.PENDING
        self.context: Dict[str, Any] = {}
        self.steps_completed: List[str] = []
        self.steps_failed: List[str] = []
        self.created_at: datetime = datetime.utcnow()
        self.updated_at: datetime = datetime.utcnow()
        self.error: Optional[str] = None
        self.result: Optional[Any] = None

    def update_context(self, key: str, value: Any) -> None:
        self.context[key] = value
        self.updated_at = datetime.utcnow()

    def mark_step_complete(self, step_name: str) -> None:
        self.steps_completed.append(step_name)
        self.updated_at = datetime.utcnow()

    def mark_step_failed(self, step_name: str, error: str) -> None:
        self.steps_failed.append(step_name)
        self.error = error
        self.status = WorkflowStatus.FAILED
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "context": self.context,
            "steps_completed": self.steps_completed,
            "steps_failed": self.steps_failed,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "error": self.error,
            "result": self.result,
        }

    def __repr__(self) -> str:
        return f"WorkflowState(id={self.workflow_id!r}, status={self.status})"
