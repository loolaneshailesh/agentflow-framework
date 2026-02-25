"""Approvals management API routes."""
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agentflow.observability.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)
_approvals: dict = {}
_counter = 0


class ApprovalRequest(BaseModel):
    invoice_id: str
    amount: float
    vendor: str
    reason: Optional[str] = ''
    metadata: Optional[Dict[str, Any]] = {}


class ApprovalDecision(BaseModel):
    decision: str
    notes: Optional[str] = ''


@router.get('/')
async def list_approvals():
    return {'approvals': list(_approvals.values())}


@router.post('/')
async def create_approval(request: ApprovalRequest):
    global _counter
    _counter += 1
    approval_id = f'APR-{_counter:04d}'
    approval = {
        'id': approval_id,
        'invoice_id': request.invoice_id,
        'amount': request.amount,
        'vendor': request.vendor,
        'reason': request.reason,
        'status': 'pending',
        'metadata': request.metadata,
    }
    _approvals[approval_id] = approval
    logger.info('approval_created', approval_id=approval_id)
    return {'approval': approval}


@router.post('/{approval_id}/decide')
async def decide_approval(approval_id: str, decision: ApprovalDecision):
    if approval_id not in _approvals:
        raise HTTPException(status_code=404, detail=f'Approval not found: {approval_id}')
    if decision.decision not in ('approve', 'reject'):
        raise HTTPException(status_code=400, detail='decision must be approve or reject')
    _approvals[approval_id]['status'] = decision.decision + 'd'
    _approvals[approval_id]['notes'] = decision.notes
    logger.info('approval_decided', approval_id=approval_id, decision=decision.decision)
    return {'approval': _approvals[approval_id]}
