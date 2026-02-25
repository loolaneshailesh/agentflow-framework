"""Tools management API routes."""
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agentflow.tools.registry import get_registry
from agentflow.core.executor import SafeToolExecutor  # or agentflow.tools.executor if that's where it lives
from agentflow.observability.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Get shared registry instance
registry = get_registry()

# Executor that uses the registry internally
executor = SafeToolExecutor(registry)


class ToolCallRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = {}


@router.get("/")
async def list_tools():
    """List all registered tools."""
    # Adapt to your registry API: list_tools() vs list_all()
    if hasattr(registry, "list_tools"):
        tools = registry.list_tools()
    elif hasattr(registry, "list_all"):
        tools = registry.list_all()
    else:
        tools = []
    return {"tools": tools}


@router.post("/execute")
async def execute_tool(request: ToolCallRequest):
    """Execute a named tool with given arguments."""
    try:
        # SafeToolExecutor.execute(tool_name, inputs) -> dict/any
        result = await executor.execute(request.tool_name, request.arguments)
        return {"tool": request.tool_name, "result": result}
    except KeyError as e:
        # tool not found
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("tool_execute_error", tool=request.tool_name, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
