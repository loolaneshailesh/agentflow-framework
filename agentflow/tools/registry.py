# agentflow/tools/registry.py
from __future__ import annotations

import inspect
import logging
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Central registry for discovering and invoking tools."""

    def __init__(self):
        self._tools: Dict[str, Any] = {}

    def register(self, tool: Any, name: Optional[str] = None) -> None:
        """Register a tool. Accepts BaseTool instances, LangChain tools, or plain callables."""
        if callable(tool) and not hasattr(tool, "name"):
            tool_name = name or getattr(tool, "__name__", None)
            if not tool_name:
                raise ValueError("A name must be provided for callable tools without __name__")
            self._tools[tool_name] = tool
            logger.info(f"Registered callable tool: {tool_name}")
            return

        if hasattr(tool, "name"):
            tool_name = name or tool.name
            if not tool_name:
                raise ValueError("Tool has no name. Provide one explicitly.")
            self._tools[tool_name] = tool
            logger.info(f"Registered tool: {tool_name}")
            return

        raise TypeError(f"Cannot register object of type {type(tool)}. "
                        "Must be a callable, BaseTool, or LangChain StructuredTool.")

    def unregister(self, name: str) -> None:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found in registry.")
        del self._tools[name]
        logger.info(f"Unregistered tool: {name}")

    def get(self, name: str) -> Any:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found in registry.")
        return self._tools[name]

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())

    def invoke(self, name: str, inputs: Dict[str, Any]) -> Any:
        tool = self.get(name)
        try:
            if callable(tool) and not hasattr(tool, "run") and not hasattr(tool, "_run"):
                sig = inspect.signature(tool)
                params = list(sig.parameters.keys())
                if len(params) == 1:
                        return tool(inputs)
                return tool(**inputs)

            if hasattr(tool, "run"):
                return tool.run(inputs)

            if hasattr(tool, "_run"):
                return tool._run(**inputs)

            raise TypeError(f"Tool '{name}' has no callable interface.")
        except Exception as e:
            logger.error(f"Error invoking tool '{name}': {e}")
            raise

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)

    def __repr__(self) -> str:
        return f"ToolRegistry(tools={self.list_tools()})"


_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
