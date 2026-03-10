# agentflow/api/routes/chat.py
"""Chat/Agent API route - Grok LLM with persistent DB memory."""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agentflow.core.database import get_db, AgentModel, ConversationModel, MessageModel
from agentflow.llm.gateway import get_gateway, DBMemoryManager
from agentflow.observability.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    model: Optional[str] = None
    system_prompt: Optional[str] = "You are a helpful AI assistant powered by Grok."
    agent_id: Optional[str] = None
    temperature: Optional[float] = 0.7


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    model: str
    message_id: str


class AgentCreateRequest(BaseModel):
    name: str
    description: str = ""
    agent_type: str = "llm"
    model: str = "groq/llama3-70b-8192"
    system_prompt: str = "You are a helpful AI agent."
    tools: Optional[List[str]] = []
    config: Optional[Dict[str, Any]] = {}


class AgentUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    tools: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


def _serialize_agent(a: AgentModel) -> dict:
    return {
        "id": a.id,
        "name": a.name,
        "description": a.description,
        "agent_type": a.agent_type,
        "model": a.model,
        "system_prompt": a.system_prompt,
        "tools": a.tools or [],
        "config": a.config or {},
        "is_active": a.is_active,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }


# ── Chat Endpoints ──────────────────────────────────────────────────

@router.post("/chat")
async def chat(request: ChatRequest):
    """Chat with the Grok LLM with persistent memory."""
    session_id = request.session_id or str(uuid.uuid4())
    gateway = get_gateway(model=request.model, session_id=session_id)

    # Get agent config if agent_id provided
    system_prompt = request.system_prompt
    if request.agent_id:
        from agentflow.core.database import SessionLocal
        db = SessionLocal()
        try:
            agent = db.query(AgentModel).filter(AgentModel.id == request.agent_id).first()
            if agent:
                system_prompt = agent.system_prompt
                if not request.model:
                    gateway._primary_model = agent.model
        finally:
            db.close()

    try:
        reply = await gateway.achat(
            messages=[{"role": "user", "content": request.message}],
            system_prompt=system_prompt,
            temperature=request.temperature or 0.7,
        )
        return {
            "reply": reply,
            "session_id": session_id,
            "model": gateway._primary_model,
            "message_id": str(uuid.uuid4()),
        }
    except Exception as e:
        logger.error("chat_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/history/{session_id}")
async def get_history(session_id: str):
    """Get conversation history for a session."""
    memory = DBMemoryManager(session_id=session_id)
    messages = memory.load_messages()
    return {"session_id": session_id, "messages": messages, "count": len(messages)}


@router.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """Clear conversation history for a session."""
    memory = DBMemoryManager(session_id=session_id)
    memory.clear()
    return {"message": f"History cleared for session {session_id}"}


# ── Agent CRUD Endpoints ─────────────────────────────────────────────

@router.get("/agents")
async def list_agents(db: Session = Depends(get_db)):
    agents = db.query(AgentModel).order_by(AgentModel.created_at.desc()).all()
    return {"agents": [_serialize_agent(a) for a in agents], "count": len(agents)}


@router.post("/agents")
async def create_agent(request: AgentCreateRequest, db: Session = Depends(get_db)):
    from datetime import datetime
    agent = AgentModel(
        id=str(uuid.uuid4()),
        name=request.name,
        description=request.description,
        agent_type=request.agent_type,
        model=request.model,
        system_prompt=request.system_prompt,
        tools=request.tools or [],
        config=request.config or {},
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return {"agent": _serialize_agent(agent)}


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return {"agent": _serialize_agent(agent)}


@router.put("/agents/{agent_id}")
async def update_agent(agent_id: str, request: AgentUpdateRequest, db: Session = Depends(get_db)):
    from datetime import datetime
    agent = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(agent, field, value)
    agent.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(agent)
    return {"agent": _serialize_agent(agent)}


@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    db.delete(agent)
    db.commit()
    return {"message": f"Agent {agent_id} deleted"}
