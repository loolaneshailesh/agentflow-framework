"""Safe sandboxed tool executor."""
import asyncio
from typing import Any, Optional
import structlog

logger = structlog.get_logger(__name__)

EXECUTION_ALLOWLIST: set[str] = set()  # empty = allow all


class SafeToolExecutor:
    """Executes tools safely with timeout and allowlist enforcement."""

    def __init__(self, registry=None):
        self.registry = registry

    async def run(self, tool, inputs: dict[str, Any]) -> dict[str, Any]:
        if EXECUTION_ALLOWLIST and tool.name not in EXECUTION_ALLOWLIST:
            raise PermissionError(
                f"Tool '{tool.name}' is not in the execution allowlist."
            )
        timeout = getattr(getattr(tool, "schema", None), "timeout_seconds", None) or 30
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

    async def execute(self, tool_name: str, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool by name using the registry."""
        if self.registry is None:
            raise RuntimeError("No registry provided to SafeToolExecutor")
        tool = self.registry.get(tool_name)
        if tool is None:
            raise ValueError(f"Tool '{tool_name}' not found in registry")
        return await self.run(tool, inputs)


# Alias for backward compatibility
SafeToolExecutor = SafeToolExecutor


# Alias
ToolExecutor = SafeToolExecutor
