"""Pydantic schemas for the AgentFlow REST API."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ─── Workflow Schemas ──────────────────────────────────────────────────────────

class WorkflowCreateRequest(BaseModel):
    """Request payload to create and execute a workflow."""
    name: str = Field(..., description="Workflow name")
    description: str = Field(default="", description="Workflow description")
    tasks: List[TaskCreateRequest] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    max_retries: int = Field(default=3, ge=0, le=10)
    timeout_seconds: int = Field(default=300, ge=10, le=3600)


class WorkflowResponse(BaseModel):
    """Response payload for a workflow."""
    workflow_id: str
    name: str
    description: str
    status: str
    tasks_count: int
    metadata: Dict[str, Any]


# ─── Task Schemas ──────────────────────────────────────────────────────────────

class TaskCreateRequest(BaseModel):
    """Request payload to create a task within a workflow."""
    name: str = Field(..., description="Task name")
    description: str = Field(default="")
    agent_id: Optional[str] = Field(default=None, description="Agent ID to run this task")
    input_data: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list, description="List of task_ids this task depends on")
    priority: str = Field(default="medium", description="Task priority: low, medium, high, critical")
    requires_approval: bool = Field(default=False)
    max_retries: int = Field(default=3, ge=0)
    timeout_seconds: int = Field(default=60, ge=5)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskResponse(BaseModel):
    """Response payload for a task."""
    task_id: str
    name: str
    description: str
    agent_id: Optional[str]
    status: str
    priority: str
    requires_approval: bool
    dependencies: List[str]
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    error: Optional[str]
    retry_count: int


# ─── Agent Schemas ─────────────────────────────────────────────────────────────

class AgentResponse(BaseModel):
    """Response payload for an agent."""
    agent_id: str
    name: str
    description: str
    status: str
    tools_count: int
    has_memory: bool
    metadata: Dict[str, Any]


# ─── Approval Schemas ──────────────────────────────────────────────────────────

class ApprovalDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalRequest(BaseModel):
    """Request to approve or reject a pending task."""
    task_id: str
    decision: ApprovalDecision
    reason: Optional[str] = None


class ApprovalResponse(BaseModel):
    """Response after processing an approval decision."""
    task_id: str
    decision: str
    message: str


# ─── Health & Status Schemas ───────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """API health check response."""
    status: str = "ok"
    version: str
    uptime_seconds: float


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    status_code: int


# Forward reference update
WorkflowCreateRequest.model_rebuild()
