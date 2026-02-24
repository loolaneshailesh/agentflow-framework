"""FastAPI application entry point for AgentFlow Framework."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from agentflow.api.routes import agents, tools, workflows, approvals, health
from agentflow.core.config import settings
from agentflow.observability.logger import get_logger, configure_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    configure_logging(log_level=settings.log_level, json_logs=settings.json_logs)
    logger.info("agentflow_startup", version="1.0.0", model=settings.llm_model)
    yield
    logger.info("agentflow_shutdown")


def create_app() -> FastAPI:
    """Factory function to create and configure the FastAPI app."""
    app = FastAPI(
        title="AgentFlow Framework",
        description="Lightweight multi-LLM agent orchestration framework",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes
    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
    app.include_router(tools.router, prefix="/api/tools", tags=["tools"])
    app.include_router(workflows.router, prefix="/api/workflows", tags=["workflows"])
    app.include_router(approvals.router, prefix="/api/approvals", tags=["approvals"])

    # Serve frontend static files
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
    if os.path.exists(frontend_path):
        app.mount("/static", StaticFiles(directory=frontend_path), name="static")

        @app.get("/", include_in_schema=False)
        async def serve_frontend():
            return FileResponse(os.path.join(frontend_path, "index.html"))

    return app


app = create_app()
