"""Health check API routes."""
from fastapi import APIRouter
from agentflow.core.config import settings

router = APIRouter()


@router.get('/health')
def health():
    return {
        'status': 'ok',
        'version': getattr(settings, 'appversion', '1.0.0'),
        'name': getattr(settings, 'appname', 'AgentFlow Framework'),
    }


@router.get('/health/detail')
def detailed_health():
    return {
        'status': 'ok',
        'version': getattr(settings, 'appversion', '1.0.0'),
        'name': getattr(settings, 'appname', 'AgentFlow Framework'),
        'debug': getattr(settings, 'debug', False),
        'checks': {
            'database': 'unknown',
            'llm_gateway': 'unknown',
            'memory': 'enabled' if getattr(settings, 'enablememory', True) else 'disabled',
        },
    }
