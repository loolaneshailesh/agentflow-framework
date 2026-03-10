# agentflow/api/main.py
"""FastAPI application entry point for AgentFlow Framework."""
from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from agentflow.core.config import settings
from agentflow.observability.logger import get_logger, configure_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    configure_logging(
        log_level=getattr(settings, "log_level", "INFO"),
        json_logs=getattr(settings, "jsonlogs", False),
    )
    # Initialize database tables on startup
    from agentflow.core.database import init_db
    init_db()
    logger.info("agentflow_startup", version=settings.app_version, model=settings.active_llm_model)
    yield
    logger.info("agentflow_shutdown")


def create_app() -> FastAPI:
    """Create and configure the FastAPI app."""
    app = FastAPI(
        title=settings.app_name,
        description="Lightweight multi-LLM agent orchestration framework with Grok AI",
        version=settings.app_version,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Import routers
    from agentflow.api.routes.workflows import router as workflows_router
    from agentflow.api.routes.tools import router as tools_router
    from agentflow.api.routes.chat import router as chat_router
    from agentflow.api.routes.approvals import router as approvals_router
    from agentflow.api.routes.health import router as health_router

    # Mount routers
    app.include_router(health_router, prefix="/api", tags=["health"])
    app.include_router(workflows_router, prefix="/api/workflows", tags=["workflows"])
    app.include_router(tools_router, prefix="/api/tools", tags=["tools"])
    app.include_router(chat_router, prefix="/api", tags=["chat", "agents"])
    app.include_router(approvals_router, prefix="/api/approvals", tags=["approvals"])

    # Serve frontend
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
    static_dir = os.path.join(frontend_dir, "static")
    if os.path.isdir(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        index = os.path.join(frontend_dir, "index.html")
        if os.path.exists(index):
            return FileResponse(index)
        return {"message": "AgentFlow Framework API", "docs": "/docs", "version": settings.app_version}

    @app.get("/api/status")
    async def api_status():
        return {
            "status": "ok",
            "version": settings.app_version,
            "model": settings.active_llm_model,
            "memory_backend": settings.memory_backend,
            "database": settings.database_url,
        }

    return app


app = create_app()
