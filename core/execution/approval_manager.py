from enum import Enum
from typing import Dict, Any, List
from core.runtime.safe_action_queue import SafeActionQueue

class ApprovalStatus(Enum):
    PENDING = "pending"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"

class ApprovalManager:
    """Compatibility facade over the durable SafeActionQueue approval store."""

    def __init__(self):
        self.queue = SafeActionQueue()

    @property
    def approvals(self) -> Dict[str, Dict[str, Any]]:
        result: Dict[str, Dict[str, Any]] = {}
        for item in self.queue.list_all(limit=500):
            if item.get("action_type") != "APPROVAL_REQUEST":
                continue
            payload = item.get("payload", {})
            task_id = payload.get("task_id")
            if not task_id:
                continue
            status = item.get("status")
            if status == "QUEUED":
                state = ApprovalStatus.AWAITING_APPROVAL
            elif status == "APPROVED":
                state = ApprovalStatus.APPROVED
            elif status == "REJECTED":
                state = ApprovalStatus.REJECTED
            else:
                state = ApprovalStatus.PENDING
            result[task_id] = {
                "status": state,
                "diff": payload.get("diff", ""),
                "risk_score": payload.get("risk_score", 0.0),
                "impact": payload.get("impact", "LOW"),
                "requested_at": item.get("created_at"),
                "decision_at": item.get("approved_at"),
                "reason": item.get("error_message"),
            }
        return result

    def request_approval(self, task_id: str, diff: str, risk_score: float = 0.0, impact: str = "LOW"):
        self.queue.request_approval(task_id, diff, risk_score, impact)
        return self.queue.get_approval(task_id) or {}

    def approve(self, task_id: str):
        self.queue.approve_approval(task_id, operator="manual")

    def reject(self, task_id: str, reason: str = ""):
        self.queue.reject_approval(task_id, reason, operator="manual")

    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        return [
            {"task_id": task_id, **data}
            for task_id, data in self.approvals.items()
            if data["status"] == ApprovalStatus.AWAITING_APPROVAL
        ]

approval_manager = ApprovalManager()
