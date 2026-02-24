"""Human-in-the-loop approval API routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from agentflow.store.approval import approval_queue
from agentflow.observability.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class ApprovalDecision(BaseModel):
    comment: Optional[str] = ""


class RejectionDecision(BaseModel):
    reason: Optional[str] = ""


@router.get("/")
async def list_approvals():
    """List all approval requests."""
    return {"approvals": approval_queue.list_all()}


@router.get("/pending")
async def list_pending_approvals():
    """List pending approval requests."""
    return {"approvals": approval_queue.list_pending()}


@router.post("/{request_id}/approve")
async def approve_request(request_id: str, decision: ApprovalDecision):
    """Approve a pending request."""
    req = approval_queue.get(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found")
    req.approve(decision.comment)
    return {"status": "approved", "request_id": request_id}


@router.post("/{request_id}/reject")
async def reject_request(request_id: str, decision: RejectionDecision):
    """Reject a pending request."""
    req = approval_queue.get(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found")
    req.reject(decision.reason)
    return {"status": "rejected", "request_id": request_id}
