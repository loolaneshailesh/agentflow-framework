"""Tools management API routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional

from agentflow.tools.registry import registry
from agentflow.tools.executor import ToolExecutor
from agentflow.observability.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)
executor = ToolExecutor(registry)


class ToolCallRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = {}


@router.get("/")
async def list_tools():
    """List all registered tools."""
    return {"tools": registry.list_tools()}


@router.post("/execute")
async def execute_tool(request: ToolCallRequest):
    """Execute a named tool with given arguments."""
    try:
        result = await executor.execute(request.tool_name, request.arguments)
        return {"tool": request.tool_name, "result": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("tool_execute_error", tool=request.tool_name, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
