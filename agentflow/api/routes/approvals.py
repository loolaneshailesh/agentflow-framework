# agentflow/api/routes/approvals.py
"""Human-in-the-loop approvals management - fully DB-persisted."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agentflow.core.database import get_db, ApprovalModel
from agentflow.observability.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

# --- Pydantic Schemas ---

class ApprovalCreateRequest(BaseModel):
    tool_name: str
    inputs: Optional[Dict[str, Any]] = {}
    workflow_run_id: Optional[str] = None

class ApprovalResolveRequest(BaseModel):
    status: str  # "approved" or "rejected"
    resolver: Optional[str] = "system"

# --- Helper ---

def _serialize_approval(a: ApprovalModel) -> Dict[str, Any]:
    return {
        "id": a.id,
        "workflow_run_id": a.workflow_run_id,
        "tool_name": a.tool_name,
        "inputs": a.inputs,
        "status": a.status,
        "requested_at": a.requested_at,
        "resolved_at": a.resolved_at,
        "resolver": a.resolver
    }

# --- Routes ---

@router.get("/")
async def list_approvals(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(ApprovalModel)
    if status:
        query = query.filter(ApprovalModel.status == status)
    approvals = query.order_by(ApprovalModel.requested_at.desc()).all()
    return {"approvals": [_serialize_approval(a) for a in approvals]}

@router.post("/")
async def create_approval(request: ApprovalCreateRequest, db: Session = Depends(get_db)):
    approval = ApprovalModel(
        id=str(uuid.uuid4()),
        tool_name=request.tool_name,
        inputs=request.inputs,
        workflow_run_id=request.workflow_run_id,
        status="pending",
        requested_at=datetime.utcnow()
    )
    db.add(approval)
    db.commit()
    db.refresh(approval)
    logger.info("approval_created", id=approval.id, tool=request.tool_name)
    return {"approval": _serialize_approval(approval)}

@router.get("/{approval_id}")
async def get_approval(approval_id: str, db: Session = Depends(get_db)):
    approval = db.query(ApprovalModel).filter(ApprovalModel.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return {"approval": _serialize_approval(approval)}

@router.post("/{approval_id}/resolve")
async def resolve_approval(approval_id: str, request: ApprovalResolveRequest, db: Session = Depends(get_db)):
    approval = db.query(ApprovalModel).filter(ApprovalModel.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status != "pending":
        raise HTTPException(status_code=400, detail=f"Approval already {approval.status}")
    if request.status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="Status must be 'approved' or 'rejected'")
    
    approval.status = request.status
    approval.resolved_at = datetime.utcnow()
    approval.resolver = request.resolver
    db.commit()
    db.refresh(approval)
    logger.info("approval_resolved", id=approval_id, status=request.status)
    return {"approval": _serialize_approval(approval)}

@router.get("/pending/count")
async def pending_approvals_count(db: Session = Depends(get_db)):
    count = db.query(ApprovalModel).filter(ApprovalModel.status == "pending").count()
    return {"pending_count": count}
