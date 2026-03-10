# agentflow/core/database.py
"""SQLAlchemy database setup with all ORM models for AgentFlow."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, Integer, JSON, ForeignKey, create_engine
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
from sqlalchemy.pool import StaticPool

from agentflow.core.config import get_settings

Base = declarative_base()
settings = get_settings()


def get_engine():
    db_url = settings.database_url
    if db_url.startswith("sqlite"):
        return create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(db_url)


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)


# ─── ORM Models ──────────────────────────────────────────────────────────────

class WorkflowModel(Base):
    __tablename__ = "workflows"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    nodes = Column(JSON, default=list)   # ReactFlow nodes
    edges = Column(JSON, default=list)   # ReactFlow edges
    config = Column(JSON, default=dict)
    status = Column(String, default="created")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    runs = relationship("WorkflowRunModel", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowRunModel(Base):
    __tablename__ = "workflow_runs"

    id = Column(String, primary_key=True)
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=False)
    status = Column(String, default="pending")
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    workflow = relationship("WorkflowModel", back_populates="runs")


class ToolModel(Base):
    __tablename__ = "tools"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, default="")
    tool_type = Column(String, default="custom")  # builtin | custom | llm
    parameters = Column(JSON, default=dict)  # JSON Schema
    code = Column(Text, nullable=True)  # Python code for dynamic tools
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentModel(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    agent_type = Column(String, default="llm")  # llm | tool | router
    model = Column(String, default="groq/llama3-70b-8192")
    system_prompt = Column(Text, default="You are a helpful AI agent.")
    tools = Column(JSON, default=list)  # list of tool names
    config = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConversationModel(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True)
    session_id = Column(String, nullable=False, index=True)
    agent_id = Column(String, nullable=True)
    workflow_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("MessageModel", back_populates="conversation", cascade="all, delete-orphan")


class MessageModel(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)  # user | assistant | system | tool
    content = Column(Text, nullable=False)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("ConversationModel", back_populates="messages")


class ApprovalModel(Base):
    __tablename__ = "approvals"

    id = Column(String, primary_key=True)
    workflow_run_id = Column(String, nullable=True)
    tool_name = Column(String, nullable=False)
    inputs = Column(JSON, default=dict)
    status = Column(String, default="pending")  # pending | approved | rejected
    requested_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolver = Column(String, nullable=True)
