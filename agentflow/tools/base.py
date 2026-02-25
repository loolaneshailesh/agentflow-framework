# agentflow/tools/base.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseTool(ABC):
    """Abstract base class for all AgentFlow tools."""

    name: str = ""
    description: str = ""

    @abstractmethod
    def _run(self, **kwargs: Any) -> Any:
        raise NotImplementedError

    def run(self, inputs: Any) -> Any:
        if isinstance(inputs, dict):
            return self._run(**inputs)
        return self._run(input=inputs)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"


AgentFlowTool = BaseTool
