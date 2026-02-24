import asyncio
from typing import Any
from agentflow.tools.base import BaseTool
import structlog

logger = structlog.get_logger(__name__)

EXECUTION_ALLOWLIST: set[str] = set()  # empty = allow all


class SafeToolExecutor:
    async def run(self, tool: BaseTool, inputs: dict[str, Any]) -> dict[str, Any]:
        if EXECUTION_ALLOWLIST and tool.name not in EXECUTION_ALLOWLIST:
            raise PermissionError(f"Tool '{tool.name}' is not in the execution allowlist.")

        timeout = tool.schema.timeout_seconds
        try:
            result = await asyncio.wait_for(tool.execute(inputs), timeout=timeout)
            logger.info("tool_executed", tool=tool.name, success=True)
            return result
        except asyncio.TimeoutError:
            logger.error("tool_timeout", tool=tool.name, timeout=timeout)
            raise TimeoutError(f"Tool '{tool.name}' timed out after {timeout}s")
        except Exception as exc:
            logger.error("tool_error", tool=tool.name, error=str(exc))
            raise
