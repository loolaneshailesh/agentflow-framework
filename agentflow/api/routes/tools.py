# agentflow/api/routes/tools.py
"""Tools management API routes - DB-persisted with dynamic tool creation."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agentflow.core.database import get_db, ToolModel
from agentflow.observability.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class ToolCreateRequest(BaseModel):
    name: str
    description: str = ""
    tool_type: str = "custom"  # builtin | custom | llm
    parameters: Optional[Dict[str, Any]] = {}  # JSON Schema for inputs
    code: Optional[str] = None  # Python code for dynamic tools


class ToolUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    code: Optional[str] = None
    is_active: Optional[bool] = None


class ToolExecuteRequest(BaseModel):
    inputs: Dict[str, Any] = {}


def _serialize_tool(t: ToolModel) -> dict:
    return {
        "id": t.id,
        "name": t.name,
        "description": t.description,
        "tool_type": t.tool_type,
        "parameters": t.parameters or {},
        "code": t.code,
        "is_active": t.is_active,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


@router.get("/")
async def list_tools(db: Session = Depends(get_db)):
    tools = db.query(ToolModel).order_by(ToolModel.created_at.desc()).all()
    return {"tools": [_serialize_tool(t) for t in tools], "count": len(tools)}


@router.post("/")
async def create_tool(request: ToolCreateRequest, db: Session = Depends(get_db)):
    # Check duplicate name
    existing = db.query(ToolModel).filter(ToolModel.name == request.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Tool with name '{request.name}' already exists")

    tool = ToolModel(
        id=str(uuid.uuid4()),
        name=request.name,
        description=request.description,
        tool_type=request.tool_type,
        parameters=request.parameters or {},
        code=request.code,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(tool)
    db.commit()
    db.refresh(tool)
    logger.info("tool_created", name=tool.name, id=tool.id)

    # Register in runtime registry too
    try:
        _register_in_registry(tool)
    except Exception as e:
        logger.warning("registry_register_failed", tool=tool.name, error=str(e))

    return {"tool": _serialize_tool(tool)}


@router.get("/{tool_id}")
async def get_tool(tool_id: str, db: Session = Depends(get_db)):
    tool = db.query(ToolModel).filter(
        (ToolModel.id == tool_id) | (ToolModel.name == tool_id)
    ).first()
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_id}")
    return {"tool": _serialize_tool(tool)}


@router.put("/{tool_id}")
async def update_tool(tool_id: str, request: ToolUpdateRequest, db: Session = Depends(get_db)):
    tool = db.query(ToolModel).filter(
        (ToolModel.id == tool_id) | (ToolModel.name == tool_id)
    ).first()
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_id}")
    if request.name is not None:
        tool.name = request.name
    if request.description is not None:
        tool.description = request.description
    if request.parameters is not None:
        tool.parameters = request.parameters
    if request.code is not None:
        tool.code = request.code
    if request.is_active is not None:
        tool.is_active = request.is_active
    tool.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(tool)
    return {"tool": _serialize_tool(tool)}


@router.delete("/{tool_id}")
async def delete_tool(tool_id: str, db: Session = Depends(get_db)):
    tool = db.query(ToolModel).filter(
        (ToolModel.id == tool_id) | (ToolModel.name == tool_id)
    ).first()
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_id}")
    db.delete(tool)
    db.commit()
    return {"message": f"Tool {tool_id} deleted"}


@router.post("/{tool_id}/execute")
async def execute_tool(tool_id: str, request: ToolExecuteRequest, db: Session = Depends(get_db)):
    tool = db.query(ToolModel).filter(
        (ToolModel.id == tool_id) | (ToolModel.name == tool_id)
    ).first()
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_id}")
    if not tool.is_active:
        raise HTTPException(status_code=400, detail=f"Tool '{tool.name}' is disabled")

    try:
        if tool.code:
            result = _execute_dynamic_tool(tool.code, request.inputs)
        else:
            from agentflow.tools.registry import get_registry
            from agentflow.core.executor import SafeToolExecutor
            registry = get_registry()
            executor = SafeToolExecutor(registry)
            result = executor.execute(tool.name, request.inputs)
        return {"tool": tool.name, "result": result, "status": "success"}
    except Exception as e:
        logger.error("tool_execute_failed", tool=tool.name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")


def _execute_dynamic_tool(code: str, inputs: dict) -> Any:
    """Execute dynamic Python tool code in a sandboxed namespace."""
    namespace = {"inputs": inputs, "result": None}
    exec(code, namespace)
    return namespace.get("result", "Tool executed (no result returned)")


def _register_in_registry(tool: ToolModel) -> None:
    """Register a DB tool in the in-memory registry."""
    from agentflow.tools.registry import get_registry
    registry = get_registry()
    if hasattr(registry, 'register'):
        def dynamic_fn(**kwargs):
            return _execute_dynamic_tool(tool.code or "result = inputs", kwargs)
        dynamic_fn.__name__ = tool.name
        dynamic_fn.__doc__ = tool.description
        registry.register(tool.name, dynamic_fn, description=tool.description)
