from __future__ import annotations
import yaml
import json
from pathlib import Path
from pydantic import BaseModel, field_validator
from typing import Any, Optional, Literal


class RetryPolicy(BaseModel):
    max_attempts: int = 3
    backoff_seconds: float = 2.0
    backoff_multiplier: float = 2.0


class StepSpec(BaseModel):
    id: str
    name: str
    tool: str
    inputs: dict[str, Any] = {}
    depends_on: list[str] = []
    retry: RetryPolicy = RetryPolicy()
    timeout_seconds: int = 60
    requires_approval: bool = False
    on_failure: Literal["stop", "continue", "dead_letter"] = "stop"
    condition: Optional[str] = None


class WorkflowSpec(BaseModel):
    id: str
    name: str
    description: str = ""
    version: str = "1.0"
    steps: list[StepSpec]
    tags: list[str] = []

    @field_validator("steps")
    @classmethod
    def steps_not_empty(cls, v):
        if not v:
            raise ValueError("Workflow must have at least one step.")
        return v

    @classmethod
    def from_yaml(cls, path: str | Path) -> "WorkflowSpec":
        raw = Path(path).read_text()
        data = yaml.safe_load(raw)
        return cls(**data)

    @classmethod
    def from_json(cls, path: str | Path) -> "WorkflowSpec":
        raw = Path(path).read_text()
        data = json.loads(raw)
        return cls(**data)

    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowSpec":
        return cls(**data)
