"""SupervisorAgent using LangGraph + LangChain ReAct pattern."""
from __future__ import annotations
from typing import Optional
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from agentflow.llm.gateway import get_gateway
from agentflow.tools.registry import registry
import structlog

logger = structlog.get_logger(__name__)


class BaseAgent:
    name: str = "base"
    description: str = "Base agent"

    async def run(self, task: str, context: dict = {}) -> str:
        raise NotImplementedError


class SupervisorAgent(BaseAgent):
    """
    Routes tasks to registered sub-agents/tools using ReAct pattern.
    Can itself be registered as a tool in a higher-level supervisor.
    """

    name = "supervisor"
    description = "Top-level supervisor that routes tasks to specialized agents and tools."

    def __init__(
        self,
        tool_names: Optional[list[str]] = None,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ):
        self._gateway = get_gateway(model)
        self._tool_names = tool_names
        self._system_prompt = system_prompt or (
            "You are a supervisor agent. Analyze the task and route it to the most "
            "appropriate tool or sub-agent. Always explain your reasoning."
        )
        self._agent = None

    def _build_agent(self):
        from langchain_litellm import ChatLiteLLM
        lc_tools = registry.as_langchain_tools(self._tool_names)
        llm = ChatLiteLLM(model=self._gateway.active_model)
        self._agent = create_react_agent(
            model=llm,
            tools=lc_tools,
            state_modifier=self._system_prompt,
        )

    async def run(self, task: str, context: dict = {}) -> str:
        if self._agent is None:
            self._build_agent()
        messages = [HumanMessage(content=task)]
        result = await self._agent.ainvoke({"messages": messages})
        final = result["messages"][-1].content
        logger.info("supervisor_result", task=task[:80], result_len=len(final))
        return final

    def as_tool(self):
        """Register this supervisor as a tool for a higher-level supervisor."""
        registry.register_agent_as_tool(self)
        return self
