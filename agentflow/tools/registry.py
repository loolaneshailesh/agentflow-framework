"""DynamicToolRegistry - register, discover, and execute tools."""
from __future__ import annotations
from typing import Type, Optional, Callable, Union
from agentflow.tools.base import BaseTool, ToolSchema
import structlog

logger = structlog.get_logger(__name__)


class DynamicToolRegistry:
    """Singleton registry. Tools self-register at import time."""

    _instance: Optional["DynamicToolRegistry"] = None

    def __init__(self):
        self._tools: dict[str, object] = {}

    @classmethod
    def get_instance(cls) -> "DynamicToolRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, tool) -> None:
        """Accept BaseTool, LangChain StructuredTool, or plain function."""
        if isinstance(tool, BaseTool):
            # Native AgentFlow BaseTool
            name = tool.name
            tags = tool.schema.tags
        elif hasattr(tool, 'name') and isinstance(getattr(tool, 'name', None), str):
            # LangChain StructuredTool or any object with a .name string attribute
            name = tool.name
            tags = getattr(tool, 'tags', []) or []
        elif callable(tool):
            # Plain Python function
            name = getattr(tool, '__name__', repr(tool))
            tags = []
        else:
            # Fallback - store it anyway
            name = repr(tool)
            tags = []
        self._tools[name] = tool
        logger.info("tool_registered", tool=name, tags=tags)

    def register_class(self, tool_cls: Type[BaseTool]) -> None:
        self.register(tool_cls())

    def get(self, name: str) -> object:
        if name not in self._tools:
            raise KeyError(
                f"Tool '{name}' not found. Available: {list(self._tools)}"
            )
        return self._tools[name]

    def list_all(self) -> list:
        result = []
        for t in self._tools.values():
            if isinstance(t, BaseTool):
                result.append(t.schema)
            elif hasattr(t, 'name'):
                result.append({"name": t.name})
            else:
                result.append({"name": getattr(t, '__name__', str(t))})
        return result

    def list_agents(self) -> list[str]:
        return list(self._tools.keys())

    async def execute(self, name: str, inputs: dict) -> dict:
        tool = self.get(name)
        if isinstance(tool, BaseTool):
            from agentflow.tools.executor import SafeToolExecutor
            return await SafeToolExecutor().run(tool, inputs)
        elif hasattr(tool, 'arun'):
            # LangChain StructuredTool
            result = await tool.arun(inputs)
            return {"result": result}
        elif hasattr(tool, 'run'):
            # LangChain sync tool
            result = tool.run(inputs)
            return {"result": result}
        elif callable(tool):
            import inspect
            if inspect.iscoroutinefunction(tool):
                return await tool(**inputs)
            else:
                return tool(**inputs)
        raise TypeError(f"Tool '{name}' is not executable")

    def as_langchain_tools(self, names: Optional[list[str]] = None):
        targets = names or list(self._tools)
        result = []
        for n in targets:
            if n not in self._tools:
                continue
            t = self._tools[n]
            if isinstance(t, BaseTool):
                result.append(t.to_langchain_tool())
            elif hasattr(t, 'run') or hasattr(t, 'arun'):
                # Already a LangChain tool
                result.append(t)
        return result

    def register_agent_as_tool(self, agent) -> None:
        from agentflow.tools.base import ToolSchema

        class AgentTool(BaseTool):
            @property
            def schema(self_inner) -> ToolSchema:
                return ToolSchema(
                    name=agent.name,
                    description=agent.description,
                    input_schema={
                        "properties": {"task": {"type": "string"}},
                        "required": ["task"]
                    },
                    output_schema={
                        "properties": {"result": {"type": "string"}}
                    },
                    tags=["agent"],
                )

            async def execute(self_inner, inputs: dict) -> dict:
                result = await agent.run(inputs["task"])
                return {"result": result}

        self.register(AgentTool())


registry = DynamicToolRegistry.get_instance()
