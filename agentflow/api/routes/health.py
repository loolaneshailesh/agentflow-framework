"""Health check endpoints."""
from fastapi import APIRouter
from agentflow.llm.gateway import LLMGateway
from agentflow.tools.registry import registry

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check."""
    return {"status": "ok", "service": "agentflow-framework"}


@router.get("/health/detail")
async def detailed_health():
    """Detailed health including LLM and tool registry status."""
    gateway = LLMGateway()
    return {
        "status": "ok",
        "active_model": gateway.active_model,
        "provider": gateway.provider,
        "registered_tools": registry.list_tools(),
        "registered_agents": registry.list_agents(),
    }
