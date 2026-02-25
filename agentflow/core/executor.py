# agentflow/core/executor.py
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

from agentflow.core.state import WorkflowState
from agentflow.tools.registry import get_registry

logger = logging.getLogger(__name__)


class SafeToolExecutor:
    """Executes tools safely with error isolation."""

    def __init__(self, registry=None):
        self.registry = registry or get_registry()

    def execute(self, tool_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        try:
            logger.info(f"Executing tool: {tool_name} with inputs: {inputs}")
            result = self.registry.invoke(tool_name, inputs)
            return {"status": "success", "tool": tool_name, "result": result}
        except KeyError as e:
            logger.error(f"Tool not found: {e}")
            return {"status": "error", "tool": tool_name, "error": f"Tool not found: {e}"}
        except Exception as e:
            logger.error(f"Tool execution failed [{tool_name}]: {e}")
            return {"status": "error", "tool": tool_name, "error": str(e)}

    async def execute_async(self, tool_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.execute, tool_name, inputs)


ToolExecutor = SafeToolExecutor
