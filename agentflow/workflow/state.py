from __future__ import annotations
from typing import Any, Optional
from typing_extensions import TypedDict


class StepState(TypedDict):
    step_id: str
    status: str  # pending | running | success | failed | awaiting_approval
    output: dict
    error: Optional[str]
    attempts: int
    started_at: Optional[str]
    completed_at: Optional[str]


class WorkflowState(TypedDict):
    run_id: str
    workflow_id: str
    status: str  # running | paused | completed | failed | cancelled
    inputs: dict[str, Any]
    steps: dict[str, StepState]
    current_step: Optional[str]
    pending_approval: Optional[dict]
    audit_events: list[dict]
    error: Optional[str]
    metadata: dict[str, Any]


# Alias for backward compatibility
from agentflow.core.engine import WorkflowEngine


# Alias - WorkflowEngine lives in core.engine
from agentflow.core.engine import WorkflowEngine
