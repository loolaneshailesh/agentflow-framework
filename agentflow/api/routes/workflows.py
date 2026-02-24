"""Workflow execution API routes."""
import yaml
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional

from agentflow.workflow.spec import WorkflowSpec
from agentflow.workflow.state import WorkflowEngine
from agentflow.observability.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class WorkflowRunRequest(BaseModel):
    workflow_name: str
    inputs: Dict[str, Any] = {}


@router.get("/")
async def list_workflows():
    """List available workflow YAML files."""
    workflows_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "workflows"
    )
    if not os.path.exists(workflows_dir):
        return {"workflows": []}
    files = [f.replace(".yaml", "") for f in os.listdir(workflows_dir) if f.endswith(".yaml")]
    return {"workflows": files}


@router.post("/run")
async def run_workflow(request: WorkflowRunRequest):
    """Load and execute a workflow by name."""
    workflows_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "workflows"
    )
    workflow_file = os.path.join(workflows_dir, f"{request.workflow_name}.yaml")
    if not os.path.exists(workflow_file):
        raise HTTPException(status_code=404, detail=f"Workflow '{request.workflow_name}' not found")
    try:
        with open(workflow_file) as f:
            spec_data = yaml.safe_load(f)
        spec = WorkflowSpec(**spec_data)
        engine = WorkflowEngine(spec)
        result = await engine.run(request.inputs)
        return {"workflow": request.workflow_name, "result": result}
    except Exception as e:
        logger.error("workflow_run_error", workflow=request.workflow_name, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
