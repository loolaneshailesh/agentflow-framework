"""Agent management API routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional

from agentflow.agents.supervisor import SupervisorAgent
from agentflow.tools.registry import registry
from agentflow.store.memory import memory_store
from agentflow.observability.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class RunRequest(BaseModel):
    task: str
    context: Optional[Dict[str, Any]] = {}
    agent_name: Optional[str] = "supervisor"


class RunResponse(BaseModel):
    result: str
    agent: str
    task: str


@router.get("/")
async def list_agents():
    """List all registered agents."""
    return {"agents": registry.list_agents()}


@router.post("/run")
async def run_agent(request: RunRequest):
    """Run the supervisor agent on a task."""
    try:
        agent = SupervisorAgent()
        result = await agent.run(request.task, request.context or {})
        memory_store.set(f"last_result_{request.agent_name}", result)
        return RunResponse(result=result, agent=request.agent_name, task=request.task)
    except Exception as e:
        logger.error("agent_run_error", error=str(e), task=request.task)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory")
async def get_memory_snapshot():
    """Return current memory store snapshot."""
    return {"memory": memory_store.snapshot()}
