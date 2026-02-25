"""Agent management API routes."""
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agentflow.agents.supervisor import SupervisorAgent
from agentflow.tools.registry import get_registry
from agentflow.observability.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Get the singleton registry instance
registry = get_registry()

# Simple in-memory store (since agentflow.store.memory was removed/changed)
_memory: dict = {}


class _MemoryStore:
    def set(self, key: str, value: Any) -> None:
        _memory[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return _memory.get(key, default)

    def snapshot(self) -> Dict[str, Any]:
        return dict(_memory)


memory_store = _MemoryStore()


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
    # SupervisorAgent is not auto-registered, so we return a simple static list
    return {"agents": ["supervisor"]}


@router.post("/run")
async def run_agent(request: RunRequest):
    """Run the supervisor agent on a task."""
    try:
        agent = SupervisorAgent()
        result = await agent.run(request.task, request.context or {})
        memory_store.set(f"last_result_{request.agent_name}", result)
        return RunResponse(result=str(result), agent=request.agent_name, task=request.task)
    except Exception as e:
        logger.error("agent_run_error", error=str(e), task=request.task)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory")
async def get_memory_snapshot():
    """Return current memory store snapshot."""
    return {"memory": memory_store.snapshot()}
