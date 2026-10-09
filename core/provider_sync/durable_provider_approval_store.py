# Path: C:\ProgramasGodMode\DGM-MAT\core\provider_sync\durable_provider_approval_store.py
"""Atomic single-use claim and audit records for durable provider approvals."""
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

    def request_provider_approval(
        self,
        *,
        task_id: str,
        provider_request_fingerprint: str,
        summary: str,
        provider_id: str,
        request_id: str,
        messages: list[dict[str, str]],
        risk_score: float = 0.0,
        impact: str = "MEDIUM",
    ) -> int:
        """Persist the exact bounded request envelope that the operator must review."""
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("task_id is required")
        if not isinstance(provider_request_fingerprint, str) or not provider_request_fingerprint.strip():
            raise ValueError("provider request fingerprint is required")
        if not isinstance(provider_id, str) or not provider_id.strip():
            raise ValueError("provider_id is required")
        if not isinstance(request_id, str) or not request_id.strip():
            raise ValueError("request_id is required")
        if not isinstance(messages, list) or not messages:
            raise ValueError("bounded provider messages are required")
        return self._queue.enqueue("APPROVAL_REQUEST", {
            "task_id": task_id.strip(),
            "diff": summary,
            "risk_score": risk_score,
            "impact": impact,
            "provider_request_fingerprint": provider_request_fingerprint,
            "provider_id": provider_id.strip(),
            "request_id": request_id.strip(),
            "messages": messages,
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
                if payload.get("provider_request_fingerprint") != expected_fingerprint:
                    return False
                audit = json.loads(action.audit_trail)
                audit.append({
                    "timestamp": datetime.now().isoformat(),
                    "event": "PROVIDER_APPROVAL_CLAIMED",
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

    def record_execution_outcome(
        self,
        task_id: str,
        *,
        success: bool,
        code: str,
        elapsed_ms: Optional[float],
    ) -> bool:
        """Append a non-sensitive result summary without storing provider response text."""
        if type(success) is not bool or not isinstance(code, str) or not code:
            return False
        try:
            with SessionLocal() as session:
                actions = session.query(ActionRecord).filter(
                    ActionRecord.action_type == "APPROVAL_REQUEST",
                    ActionRecord.status == ActionStatus.RUNNING,
                ).all()
                action = None
                for candidate in actions:
                    payload = json.loads(candidate.payload)
                    if payload.get("task_id") == task_id and payload.get("provider_request_fingerprint"):
                        action = candidate
                        break
                if action is None:
                    return False
                audit = json.loads(action.audit_trail)
                audit.append({
                    "timestamp": datetime.now().isoformat(),
                    "event": "PROVIDER_EXECUTION_RESULT",
                    "success": success,
                    "code": code[:128],
                    "elapsed_ms": round(elapsed_ms, 3) if isinstance(elapsed_ms, (int, float)) else None,
                })
                action.audit_trail = json.dumps(audit)
                action.status = ActionStatus.COMPLETED if success else ActionStatus.FAILED
                if not success:
                    action.error_message = code[:128]
                session.commit()
                return True
        except Exception:
            return False
