# agentflow/api/routes/agents.py
"""Agent management API routes - fully DB-persisted."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agentflow.core.database import get_db, AgentModel
from agentflow.observability.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

# --- Pydantic Schemas ---

class AgentCreateRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    agent_type: Optional[str] = "llm"
    model: Optional[str] = "groq/llama-3.1-8b-instant"
    system_prompt: Optional[str] = "You are a helpful AI agent."
    tools: Optional[List[str]] = []
    config: Optional[Dict[str, Any]] = {}

class AgentUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    agent_type: Optional[str] = None
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    tools: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class AgentRunRequest(BaseModel):
    task: str
    context: Optional[Dict[str, Any]] = {}

# --- Helper ---

def _serialize_agent(agent: AgentModel) -> Dict[str, Any]:
    return {
        "id": agent.id,
        "name": agent.name,
        "description": agent.description,
        "agent_type": agent.agent_type,
        "model": agent.model,
        "system_prompt": agent.system_prompt,
        "tools": agent.tools,
        "config": agent.config,
        "is_active": agent.is_active,
        "created_at": agent.created_at,
        "updated_at": agent.updated_at
    }

# --- Routes ---

@router.get("/")
async def list_agents(db: Session = Depends(get_db)):
    agents = db.query(AgentModel).filter(AgentModel.is_active == True).all()
    return {"agents": [_serialize_agent(a) for a in agents]}

@router.post("/")
async def create_agent(request: AgentCreateRequest, db: Session = Depends(get_db)):
    agent_id = str(uuid.uuid4())
    agent = AgentModel(
        id=agent_id,
        name=request.name,
        description=request.description,
        agent_type=request.agent_type,
        model=request.model,
        system_prompt=request.system_prompt,
        tools=request.tools,
        config=request.config
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    logger.info("agent_created", id=agent_id, name=request.name)
    return {"agent": _serialize_agent(agent)}

@router.get("/{agent_id}")
async def get_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"agent": _serialize_agent(agent)}

@router.put("/{agent_id}")
async def update_agent(agent_id: str, request: AgentUpdateRequest, db: Session = Depends(get_db)):
    agent = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if request.name is not None: agent.name = request.name
    if request.description is not None: agent.description = request.description
    if request.agent_type is not None: agent.agent_type = request.agent_type
    if request.model is not None: agent.model = request.model
    if request.system_prompt is not None: agent.system_prompt = request.system_prompt
    if request.tools is not None: agent.tools = request.tools
    if request.config is not None: agent.config = request.config
    if request.is_active is not None: agent.is_active = request.is_active
    
    agent.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(agent)
    logger.info("agent_updated", id=agent_id)
    return {"agent": _serialize_agent(agent)}

@router.delete("/{agent_id}")
async def delete_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.is_active = False
    agent.updated_at = datetime.utcnow()
    db.commit()
    return {"message": f"Agent {agent_id} deactivated"}

@router.post("/{agent_id}/run")
async def run_agent(agent_id: str, request: AgentRunRequest, db: Session = Depends(get_db)):
    """Run a specific DB-registered agent on a task."""
    agent = db.query(AgentModel).filter(AgentModel.id == agent_id, AgentModel.is_active == True).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found or inactive")
    
    try:
        from agentflow.agents.supervisor import SupervisorAgent
        executor = SupervisorAgent()
        result = await executor.run(request.task, {
            "agent_model": agent.model,
            "system_prompt": agent.system_prompt,
            **request.context
        })
        logger.info("agent_run_success", id=agent_id, task=request.task[:50])
        return {"agent_id": agent_id, "result": str(result), "task": request.task}
    except Exception as e:
        logger.error("agent_run_error", id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
