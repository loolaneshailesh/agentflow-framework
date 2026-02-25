"""FastAPI application entry point for AgentFlow Framework."""
from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from agentflow.api.routes import agents, tools, workflows, approvals, health
from agentflow.core.config import settings
from agentflow.observability.logger import get_logger, configure_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle for the AgentFlow API."""
    # Configure logging once at startup
    configure_logging(
        log_level=getattr(settings, "loglevel", "INFO"),
        json_logs=getattr(settings, "jsonlogs", False),
    )
    logger.info(
        "agentflow_startup",
        version=getattr(settings, "appversion", "1.0.0"),
        model=getattr(settings, "llmmodel", "gpt-4o"),
    )
    try:
        yield
    finally:
        logger.info("agentflow_shutdown")


def create_app() -> FastAPI:
    """Factory function to create and configure the FastAPI app."""
    app = FastAPI(
        title=getattr(settings, "appname", "AgentFlow Framework"),
        description="Lightweight multi-LLM agent orchestration framework",
        version=getattr(settings, "appversion", "1.0.0"),
        lifespan=lifespan,
    )

    # CORS for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[getattr(settings, "corsorigins", "http://localhost:5173")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes (health router should define /health and /health/detail)
    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
    app.include_router(tools.router, prefix="/api/tools", tags=["tools"])
    app.include_router(workflows.router, prefix="/api/workflows", tags=["workflows"])
    app.include_router(approvals.router, prefix="/api/approvals", tags=["approvals"])

    # Serve frontend static files (simple SPA)
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
    frontend_path = os.path.abspath(frontend_path)

    if os.path.isdir(frontend_path):
        static_dir = os.path.join(frontend_path, "static")
        if os.path.isdir(static_dir):
            app.mount("/static", StaticFiles(directory=static_dir), name="static")

        @app.get("/", include_in_schema=False)
        async def serve_frontend_index():
            index_file = os.path.join(frontend_path, "index.html")
            if os.path.exists(index_file):
                return FileResponse(index_file)
            # Fallback JSON if index.html is missing
            return {
                "message": "AgentFlow API is running",
                "docs": "/docs",
                "health": "/api/health",
            }

    return app


app = create_app()
