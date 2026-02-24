"""Tool-calling agent for AgentFlow - executes tasks via registered tools."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from agentflow.agents.base import BaseAgent
from agentflow.core.agent import AgentStatus

logger = logging.getLogger(__name__)


@dataclass
class ToolAgent(BaseAgent):
    """An agent that executes tasks by selecting and running registered tools."""

    tool_registry: Dict[str, Any] = field(default_factory=dict)
    fallback_model: str = "gpt-4o-mini"

    def register_tool(self, name: str, tool: Any) -> None:
        """Register a named tool with this agent."""
        self.tool_registry[name] = tool
        logger.info(f"ToolAgent '{self.name}' registered tool: {name}")

    async def run(self, task: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute the task by running the appropriate tool."""
        context = context or {}
        self.status = AgentStatus.RUNNING
        logger.info(f"ToolAgent '{self.name}' running task: {task.name}")

        try:
            # Determine which tool to use from task metadata or input_data
            tool_name = task.metadata.get("tool") or task.input_data.get("tool")

            if tool_name and tool_name in self.tool_registry:
                result = await self._run_tool(tool_name, task, context)
            else:
                # Fallback: run all tools sequentially
                result = await self._run_all_tools(task, context)

            self.status = AgentStatus.COMPLETED
            return result

        except Exception as e:
            self.status = AgentStatus.FAILED
            logger.error(f"ToolAgent '{self.name}' failed: {e}")
            raise

    async def _run_tool(self, tool_name: str, task: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run a specific tool by name."""
        tool = self.tool_registry[tool_name]
        logger.info(f"Running tool: {tool_name}")

        tool_input = {**task.input_data, **context}

        if hasattr(tool, "arun"):
            result = await tool.arun(tool_input)
        elif hasattr(tool, "run"):
            result = tool.run(tool_input)
        elif callable(tool):
            result = tool(tool_input)
        else:
            raise ValueError(f"Tool '{tool_name}' is not callable")

        return {
            "tool": tool_name,
            "result": result,
            "task_name": task.name,
        }

    async def _run_all_tools(self, task: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run all registered tools and aggregate results."""
        results = {}
        for name, tool in self.tool_registry.items():
            try:
                r = await self._run_tool(name, task, context)
                results[name] = r["result"]
            except Exception as e:
                logger.warning(f"Tool '{name}' failed: {e}")
                results[name] = {"error": str(e)}

        return {"results": results, "task_name": task.name}

    def list_tools(self) -> List[str]:
        """Return names of all registered tools."""
        return list(self.tool_registry.keys())
