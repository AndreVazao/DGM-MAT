# Path: C:\\ProgramasGodMode\\DGM-MAT\\core\\provider_sync\\durable_provider_approval_store.py
"""Atomic single-use claim for durable provider approval records."""
import json
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import update

from core.runtime.safe_action_queue import ActionStatus, SafeActionQueue
from core.storage.database import SessionLocal
from core.storage.models import ActionRecord


class DurableProviderApprovalStore:
    """Read durable approvals and atomically consume one approved task."""

    def __init__(self, queue: Optional[SafeActionQueue] = None) -> None:
        self._queue = queue if queue is not None else SafeActionQueue()

    def get_approval(self, task_id: str) -> Optional[Dict[str, Any]]:
        approval = self._queue.get_approval(task_id)
        if not isinstance(approval, dict):
            return None
        payload = approval.get("payload", {})
        if isinstance(payload, dict):
            approval["provider_request_fingerprint"] = payload.get("provider_request_fingerprint")
        return approval

    def request_provider_approval(self, *, task_id: str, provider_request_fingerprint: str, summary: str, risk_score: float = 0.0, impact: str = "MEDIUM") -> int:
        if not task_id.strip() or not provider_request_fingerprint.strip():
            raise ValueError("task_id and request fingerprint are required")
        return self._queue.enqueue("APPROVAL_REQUEST", {
            "task_id": task_id.strip(),
            "diff": summary,
            "risk_score": risk_score,
            "impact": impact,
            "provider_request_fingerprint": provider_request_fingerprint,
        })

    def claim_approval(self, task_id: str, expected_fingerprint: str) -> bool:
        """Transition one approved, non-executable approval record to RUNNING once."""
        approval = self.get_approval(task_id)
        if not isinstance(approval, dict) or approval.get("status") != "APPROVED":
            return False
        if not approval.get("approved_by") or not approval.get("approved_at"):
            return False
        if approval.get("provider_request_fingerprint") != expected_fingerprint:
            return False
        action_id = approval.get("id")
        if not isinstance(action_id, int):
            return False
        try:
            with SessionLocal() as session:
                action = session.get(ActionRecord, action_id)
                if action is None or action.action_type != "APPROVAL_REQUEST":
                    return False
                payload = json.loads(action.payload)
                if payload.get("task_id") != task_id:
                    return False
                audit = json.loads(action.audit_trail)
                audit.append({
                    "timestamp": datetime.now().isoformat(),
                    "status": "RUNNING",
                    "message": "Durable provider approval claimed for one execution",
                })
                result = session.execute(
                    update(ActionRecord)
                    .where(
                        ActionRecord.id == action_id,
                        ActionRecord.action_type == "APPROVAL_REQUEST",
                        ActionRecord.status == ActionStatus.APPROVED,
                        ActionRecord.is_approved.is_(False),
                    )
                    .values(status=ActionStatus.RUNNING, audit_trail=json.dumps(audit))
                )
                if result.rowcount != 1:
                    session.rollback()
                    return False
                session.commit()
                return True
        except Exception:
            return False
