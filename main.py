# main.py
"""AgentFlow Framework - FastAPI Application Entry Point."""

from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from agentflow.core.config import get_settings
from agentflow.core.logger import configure_logging

settings = get_settings()
configure_logging(level=settings.log_level)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Lightweight AI Agent Orchestration Framework",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok", "version": settings.app_version}


@app.get("/api/tools")
def list_tools():
    from agentflow.tools.registry import get_registry
    registry = get_registry()
    return {"tools": registry.list_tools(), "count": len(registry)}


@app.post("/api/tools/{tool_name}/invoke")
def invoke_tool(tool_name: str, payload: dict):
    from agentflow.tools.registry import get_registry
    from agentflow.core.executor import SafeToolExecutor
    registry = get_registry()
    executor = SafeToolExecutor(registry)
    result = executor.execute(tool_name, payload.get("inputs", {}))
    return result


@app.get("/api/workflows")
def list_workflows():
    return {"workflows": [], "message": "Workflow engine ready"}


@app.post("/api/workflows/run")
def run_workflow(payload: dict):
    from agentflow.core.state import WorkflowState, WorkflowStatus
    state = WorkflowState()
    state.status = WorkflowStatus.RUNNING
    for k, v in payload.items():
        state.update_context(k, v)
    state.status = WorkflowStatus.COMPLETED
    state.result = {"message": "Workflow executed (demo mode)", "context": state.context}
    return state.to_dict()


FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def serve_frontend():
    index = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
