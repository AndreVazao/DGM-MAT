from enum import Enum

class ApprovalStatus(Enum):
    PENDING = "pending"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"

class ApprovalManager:
    def __init__(self):
        self.approvals = {}

    def request_approval(self, task_id: str, diff: str):
        self.approvals[task_id] = {
            "status": ApprovalStatus.AWAITING_APPROVAL,
            "diff": diff
        }
        return self.approvals[task_id]

    def approve(self, task_id: str):
        if task_id in self.approvals:
            self.approvals[task_id]["status"] = ApprovalStatus.APPROVED
