"""Human-in-the-loop approval queue for high-risk workflow steps."""
import asyncio
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from agentflow.observability.logger import get_logger

logger = get_logger(__name__)


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalRequest:
    """Represents a single approval request."""

    def __init__(
        self,
        task_id: str,
        agent_name: str,
        action: str,
        payload: Dict[str, Any],
        timeout_seconds: int = 300,
    ):
        self.id = str(uuid.uuid4())
        self.task_id = task_id
        self.agent_name = agent_name
        self.action = action
        self.payload = payload
        self.status = ApprovalStatus.PENDING
        self.created_at = datetime.utcnow().isoformat()
        self.resolved_at: Optional[str] = None
        self.timeout_seconds = timeout_seconds
        self._future: asyncio.Future = asyncio.get_event_loop().create_future()

    def approve(self, comment: str = "") -> None:
        """Approve this request."""
        self.status = ApprovalStatus.APPROVED
        self.resolved_at = datetime.utcnow().isoformat()
        if not self._future.done():
            self._future.set_result({"status": "approved", "comment": comment})
        logger.info("approval_approved", request_id=self.id, action=self.action)

    def reject(self, reason: str = "") -> None:
        """Reject this request."""
        self.status = ApprovalStatus.REJECTED
        self.resolved_at = datetime.utcnow().isoformat()
        if not self._future.done():
            self._future.set_result({"status": "rejected", "reason": reason})
        logger.info("approval_rejected", request_id=self.id, action=self.action)

    async def wait(self) -> Dict[str, Any]:
        """Wait for approval decision with timeout."""
        try:
            return await asyncio.wait_for(self._future, timeout=self.timeout_seconds)
        except asyncio.TimeoutError:
            self.status = ApprovalStatus.EXPIRED
            logger.warning("approval_expired", request_id=self.id)
            return {"status": "expired"}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "agent_name": self.agent_name,
            "action": self.action,
            "payload": self.payload,
            "status": self.status,
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
        }


class ApprovalQueue:
    """Manages all pending and resolved approval requests."""

    def __init__(self):
        self._requests: Dict[str, ApprovalRequest] = {}

    def create_request(
        self,
        task_id: str,
        agent_name: str,
        action: str,
        payload: Dict[str, Any],
        timeout_seconds: int = 300,
    ) -> ApprovalRequest:
        req = ApprovalRequest(task_id, agent_name, action, payload, timeout_seconds)
        self._requests[req.id] = req
        logger.info("approval_created", request_id=req.id, agent=agent_name, action=action)
        return req

    def get(self, request_id: str) -> Optional[ApprovalRequest]:
        return self._requests.get(request_id)

    def list_pending(self) -> List[Dict[str, Any]]:
        return [
            r.to_dict()
            for r in self._requests.values()
            if r.status == ApprovalStatus.PENDING
        ]

    def list_all(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._requests.values()]


approval_queue = ApprovalQueue()
