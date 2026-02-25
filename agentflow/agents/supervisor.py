# agentflow/agents/supervisor.py
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agentflow.tools.registry import get_registry
from agentflow.core.state import WorkflowState, WorkflowStatus

logger = logging.getLogger(__name__)


class SupervisorAgent:
    """Supervises and coordinates other agents and tools."""

    def __init__(self, name: str = "supervisor"):
        self.name = name
        self.registry = get_registry()
        self.agents: Dict[str, Any] = {}
        logger.info(f"SupervisorAgent '{self.name}' initialized")

    def register_agent(self, name: str, agent: Any) -> None:
        self.agents[name] = agent
        logger.info(f"Registered agent: {name}")

    def list_agents(self) -> List[str]:
        return list(self.agents.keys())

    def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run a task through the supervisor."""
        state = WorkflowState()
        state.status = WorkflowStatus.RUNNING
        logger.info(f"SupervisorAgent running task: {task}")

        try:
            for k, v in task.items():
                state.update_context(k, v)
            state.status = WorkflowStatus.COMPLETED
            state.result = {
                "message": "Task completed by supervisor",
                "task": task,
                "agents_available": self.list_agents(),
                "tools_available": self.registry.list_tools(),
            }
        except Exception as e:
            state.mark_step_failed("supervisor_run", str(e))
            logger.error(f"Supervisor task failed: {e}")

        return state.to_dict()

    def __repr__(self) -> str:
        return f"SupervisorAgent(name={self.name!r}, agents={self.list_agents()})"
