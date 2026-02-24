"""BaseTool ABC - all tools inherit from this."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel


class ToolSchema(BaseModel):
    name: str
    description: str
    input_schema: dict
    output_schema: dict
    tags: list[str] = []
    timeout_seconds: int = 30
    requires_approval: bool = False


class BaseTool(ABC):
    """SOLID-compliant base tool. Subclass and implement execute."""

    @property
    @abstractmethod
    def schema(self) -> ToolSchema:
        ...

    @abstractmethod
    async def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        ...

    @property
    def name(self) -> str:
        return self.schema.name

    def to_langchain_tool(self):
        """Wrap as a LangChain StructuredTool for agent binding."""
        from langchain_core.tools import StructuredTool
        from pydantic import create_model

        fields = {
            k: (str, ...) for k in self.schema.input_schema.get("properties", {})
        }
        InputModel = create_model(f"{self.name}Input", **fields)

        async def _run(**kwargs):
            return await self.execute(kwargs)

        return StructuredTool(
            name=self.name,
            description=self.schema.description,
            args_schema=InputModel,
            coroutine=_run,
        )
