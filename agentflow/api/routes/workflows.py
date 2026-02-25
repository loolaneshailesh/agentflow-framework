"""Workflow management API routes."""
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agentflow.tools.registry import get_registry
from agentflow.observability.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)
registry = get_registry()
_workflows: dict = {}


class WorkflowCreateRequest(BaseModel):
    name: str
    steps: list = []
    config: Optional[Dict[str, Any]] = {}


@router.get('/')
async def list_workflows():
    return {'workflows': list(_workflows.values())}


@router.post('/')
async def create_workflow(request: WorkflowCreateRequest):
    workflow = {
        'name': request.name,
        'steps': request.steps,
        'config': request.config,
        'status': 'created',
    }
    _workflows[request.name] = workflow
    logger.info('workflow_created', name=request.name)
    return {'workflow': workflow}


@router.get('/{workflow_name}')
async def get_workflow(workflow_name: str):
    if workflow_name not in _workflows:
        raise HTTPException(status_code=404, detail=f'Workflow not found: {workflow_name}')
    return {'workflow': _workflows[workflow_name]}
