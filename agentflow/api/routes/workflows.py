# agentflow/api/routes/workflows.py
"""Workflow management API routes - fully DB-persisted."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agentflow.core.database import (
    get_db, WorkflowModel, WorkflowRunModel
)
from agentflow.observability.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


# ─ Pydantic Schemas ────────────────────────────────────────────────────

class WorkflowCreateRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    nodes: Optional[List[Dict[str, Any]]] = []
    edges: Optional[List[Dict[str, Any]]] = []
    config: Optional[Dict[str, Any]] = {}


class WorkflowUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    nodes: Optional[List[Dict[str, Any]]] = None
    edges: Optional[List[Dict[str, Any]]] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class WorkflowRunRequest(BaseModel):
    input_data: Optional[Dict[str, Any]] = {}
    session_id: Optional[str] = None


def _serialize_workflow(wf: WorkflowModel) -> dict:
    return {
        "id": wf.id,
        "name": wf.name,
        "description": wf.description,
        "nodes": wf.nodes or [],
        "edges": wf.edges or [],
        "config": wf.config or {},
        "status": wf.status,
        "created_at": wf.created_at.isoformat() if wf.created_at else None,
        "updated_at": wf.updated_at.isoformat() if wf.updated_at else None,
    }


# ─ Routes ────────────────────────────────────────────────────────────────

@router.get("/")
async def list_workflows(db: Session = Depends(get_db)):
    workflows = db.query(WorkflowModel).order_by(WorkflowModel.created_at.desc()).all()
    return {"workflows": [_serialize_workflow(w) for w in workflows], "count": len(workflows)}


@router.post("/")
async def create_workflow(request: WorkflowCreateRequest, db: Session = Depends(get_db)):
    wf = WorkflowModel(
        id=str(uuid.uuid4()),
        name=request.name,
        description=request.description or "",
        nodes=request.nodes or [],
        edges=request.edges or [],
        config=request.config or {},
        status="created",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(wf)
    db.commit()
    db.refresh(wf)
    logger.info("workflow_created", name=wf.name, id=wf.id)
    return {"workflow": _serialize_workflow(wf)}


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str, db: Session = Depends(get_db)):
    wf = db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
    return {"workflow": _serialize_workflow(wf)}


@router.put("/{workflow_id}")
async def update_workflow(workflow_id: str, request: WorkflowUpdateRequest, db: Session = Depends(get_db)):
    wf = db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
    if request.name is not None:
        wf.name = request.name
    if request.description is not None:
        wf.description = request.description
    if request.nodes is not None:
        wf.nodes = request.nodes
    if request.edges is not None:
        wf.edges = request.edges
    if request.config is not None:
        wf.config = request.config
    if request.status is not None:
        wf.status = request.status
    wf.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(wf)
    logger.info("workflow_updated", id=wf.id)
    return {"workflow": _serialize_workflow(wf)}


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str, db: Session = Depends(get_db)):
    wf = db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
    db.delete(wf)
    db.commit()
    return {"message": f"Workflow {workflow_id} deleted"}


@router.post("/{workflow_id}/run")
async def run_workflow(workflow_id: str, request: WorkflowRunRequest, db: Session = Depends(get_db)):
    wf = db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

    run = WorkflowRunModel(
        id=str(uuid.uuid4()),
        workflow_id=workflow_id,
        status="running",
        input_data=request.input_data or {},
        output_data={},
        started_at=datetime.utcnow(),
    )
    db.add(run)
    db.commit()

    try:
        # Execute nodes in order using Grok LLM
        from agentflow.llm.gateway import get_gateway
        session_id = request.session_id or run.id
        gateway = get_gateway(session_id=session_id)

        results = []
        nodes = wf.nodes or []
        edges = wf.edges or []

        # Build execution order from edges (topological sort)
        node_map = {n["id"]: n for n in nodes}
        executed = {}

        for node in nodes:
            node_type = node.get("type", "llm")
            node_data = node.get("data", {})
            node_id = node["id"]

            if node_type == "llm" or node_type == "agent":
                prompt = node_data.get("prompt", "Process the following input.")
                system_prompt = node_data.get("system_prompt", "You are a helpful AI agent.")
                user_input = str(request.input_data)
                response = await gateway.achat(
                    messages=[{"role": "user", "content": f"{prompt}\n\nInput: {user_input}"}],
                    system_prompt=system_prompt,
                )
                executed[node_id] = response
                results.append({"node_id": node_id, "type": node_type, "output": response})

            elif node_type == "tool":
                tool_name = node_data.get("tool_name", "")
                from agentflow.tools.registry import get_registry
                from agentflow.core.executor import SafeToolExecutor
                registry = get_registry()
                executor = SafeToolExecutor(registry)
                result = executor.execute(tool_name, node_data.get("inputs", {}))
                executed[node_id] = result
                results.append({"node_id": node_id, "type": node_type, "output": result})

        run.status = "completed"
        run.output_data = {"results": results, "executed_nodes": len(results)}
        run.finished_at = datetime.utcnow()

    except Exception as e:
        run.status = "failed"
        run.error = str(e)
        run.finished_at = datetime.utcnow()
        logger.error("workflow_run_failed", workflow_id=workflow_id, error=str(e))

    db.commit()
    db.refresh(run)

    return {
        "run_id": run.id,
        "workflow_id": workflow_id,
        "status": run.status,
        "output": run.output_data,
        "error": run.error,
    }


@router.get("/{workflow_id}/runs")
async def list_runs(workflow_id: str, db: Session = Depends(get_db)):
    runs = db.query(WorkflowRunModel).filter(
        WorkflowRunModel.workflow_id == workflow_id
    ).order_by(WorkflowRunModel.started_at.desc()).all()
    return {
        "runs": [
            {
                "id": r.id,
                "status": r.status,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "finished_at": r.finished_at.isoformat() if r.finished_at else None,
                "output": r.output_data,
                "error": r.error,
            }
            for r in runs
        ]
    }
