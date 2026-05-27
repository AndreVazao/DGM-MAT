from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime

class ApprovalStatus(Enum):
    PENDING = "pending"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"

class ApprovalManager:
    def __init__(self):
        self.approvals: Dict[str, Dict[str, Any]] = {}

    def request_approval(self, task_id: str, diff: str, risk_score: float = 0.0, impact: str = "LOW"):
        """
        Registers a patch for human approval.
        """
        self.approvals[task_id] = {
            "status": ApprovalStatus.AWAITING_APPROVAL,
            "diff": diff,
            "risk_score": risk_score,
            "impact": impact,
            "requested_at": datetime.now().isoformat(),
            "decision_at": None
        }
        return self.approvals[task_id]

    def approve(self, task_id: str):
        if task_id in self.approvals:
            self.approvals[task_id]["status"] = ApprovalStatus.APPROVED
            self.approvals[task_id]["decision_at"] = datetime.now().isoformat()

    def reject(self, task_id: str, reason: str = ""):
        if task_id in self.approvals:
            self.approvals[task_id]["status"] = ApprovalStatus.REJECTED
            self.approvals[task_id]["decision_at"] = datetime.now().isoformat()
            self.approvals[task_id]["reason"] = reason

    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        return [
            {"task_id": tid, **data}
            for tid, data in self.approvals.items()
            if data["status"] == ApprovalStatus.AWAITING_APPROVAL
        ]

approval_manager = ApprovalManager()
