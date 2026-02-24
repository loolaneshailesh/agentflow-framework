"""DynamicToolRegistry - register, discover, and execute tools."""
from __future__ import annotations
from typing import Type, Optional
from agentflow.tools.base import BaseTool, ToolSchema
import structlog

logger = structlog.get_logger(__name__)


class DynamicToolRegistry:
    """Singleton registry. Tools self-register at import time."""

    _instance: Optional["DynamicToolRegistry"] = None

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    @classmethod
    def get_instance(cls) -> "DynamicToolRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool
        logger.info("tool_registered", tool=tool.name, tags=tool.schema.tags)

    def register_class(self, tool_cls: Type[BaseTool]) -> None:
        self.register(tool_cls())

    def get(self, name: str) -> BaseTool:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found. Available: {list(self._tools)}")
        return self._tools[name]

    def list_all(self) -> list[ToolSchema]:
        return [t.schema for t in self._tools.values()]

    async def execute(self, name: str, inputs: dict) -> dict:
        from agentflow.tools.executor import SafeToolExecutor
        tool = self.get(name)
        return await SafeToolExecutor().run(tool, inputs)

    def as_langchain_tools(self, names: Optional[list[str]] = None):
        targets = names or list(self._tools)
        return [self._tools[n].to_langchain_tool() for n in targets if n in self._tools]

    def register_agent_as_tool(self, agent) -> None:
        from agentflow.tools.base import ToolSchema

        class AgentTool(BaseTool):
            @property
            def schema(self_inner) -> ToolSchema:
                return ToolSchema(
                    name=agent.name,
                    description=agent.description,
                    input_schema={"properties": {"task": {"type": "string"}}, "required": ["task"]},
                    output_schema={"properties": {"result": {"type": "string"}}},
                    tags=["agent"],
                )

            async def execute(self_inner, inputs: dict) -> dict:
                result = await agent.run(inputs["task"])
                return {"result": result}

        self.register(AgentTool())


registry = DynamicToolRegistry.get_instance()
