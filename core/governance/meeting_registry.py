"""Persistent, approval-gated central governance meetings.

Meetings are governance records, not office animations. This module deliberately
records proposals and decisions but never executes the resulting actions.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_LOCK = threading.RLock()
_STATES = {"scheduled", "in_progress", "decision_pending", "approved", "rejected", "closed"}
_HIGH_IMPACT = {"cross_department_change", "architecture_change", "structural_department_change", "major_technology_change", "critical_reorganization"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_text(value: str, field: str, limit: int = 4000) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    value = value.strip()
    if len(value) > limit:
        raise ValueError(f"{field} exceeds {limit} characters")
    return value


class GovernanceMeetingRegistry:
    """Small JSON-backed registry with atomic writes and explicit decision gates."""

    def __init__(self, path: str | Path | None = None):
        configured = path or os.environ.get("DGM_GOVERNANCE_MEETINGS_PATH")
        self.path = Path(configured) if configured else Path("data/governance/meetings.json")

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema_version": 1, "meetings": {}}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError("Governance meeting store is unreadable; refusing to overwrite it.") from exc
        if not isinstance(data, dict) or data.get("schema_version") != 1 or not isinstance(data.get("meetings"), dict):
            raise RuntimeError("Governance meeting store has an unsupported schema; refusing to overwrite it.")
        return data

    def _write(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_name(self.path.name + ".tmp")
        try:
            temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            os.replace(temp, self.path)
        finally:
            try:
                temp.unlink(missing_ok=True)
            except OSError:
                pass

    def list_meetings(self) -> list[dict[str, Any]]:
        with _LOCK:
            data = self._read()
            return sorted(data["meetings"].values(), key=lambda item: item["created_at"], reverse=True)

    def list_pending_approvals(self) -> list[dict[str, Any]]:
        """Return durable approval requests that still require a human/CEO decision."""
        with _LOCK:
            meetings = self._read()["meetings"].values()
            pending = [
                item for item in meetings
                if item.get("approval", {}).get("status") == "pending"
                or item.get("owner_approval", {}).get("status") == "pending"
            ]
            return sorted(pending, key=lambda item: item["updated_at"], reverse=True)

    @staticmethod
    def _plan_digest(meeting: dict[str, Any]) -> str:
        decision = meeting.get("decision") or {}
        plan = {
            "meeting_id": meeting.get("meeting_id"),
            "meeting_type": meeting.get("meeting_type"),
            "proposal": meeting.get("proposal"),
            "agenda": meeting.get("agenda"),
            "participants": meeting.get("participants"),
            "related_departments": meeting.get("related_departments"),
            "contributions": meeting.get("contributions"),
            "outcome": decision.get("outcome"),
            "action_plan": decision.get("action_plan", ""),
        }
        canonical = json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def get_meeting(self, meeting_id: str) -> dict[str, Any]:
        with _LOCK:
            meeting = self._read()["meetings"].get(meeting_id)
            if meeting is None:
                raise KeyError(meeting_id)
            return meeting

    def create_meeting(
        self,
        *,
        title: str,
        meeting_type: str,
        requested_by: str,
        participants: list[str],
        agenda: list[str],
        proposal: str,
        related_departments: list[str] | None = None,
    ) -> dict[str, Any]:
        title = _clean_text(title, "title", 200)
        meeting_type = _clean_text(meeting_type, "meeting_type", 80)
        requested_by = _clean_text(requested_by, "requested_by", 120)
        proposal = _clean_text(proposal, "proposal")
        if not participants or not all(isinstance(p, str) and p.strip() for p in participants):
            raise ValueError("participants must contain at least one named participant")
        if not agenda or not all(isinstance(item, str) and item.strip() for item in agenda):
            raise ValueError("agenda must contain at least one item")
        participants = list(dict.fromkeys(p.strip()[:120] for p in participants))
        high_impact = meeting_type in _HIGH_IMPACT
        # High-impact governance must explicitly include the CEO as a participant.
        if high_impact and not any(p.casefold() in {"ceo", "chief executive officer"} for p in participants):
            raise ValueError("CEO participation is required for high-impact governance meetings")
        now = _now()
        meeting_id = str(uuid.uuid4())
        record = {
            "meeting_id": meeting_id,
            "title": title,
            "meeting_type": meeting_type,
            "requested_by": requested_by,
            "participants": participants,
            "related_departments": list(dict.fromkeys((related_departments or [])[:30])),
            "agenda": [_clean_text(item, "agenda item", 500) for item in agenda[:30]],
            "proposal": proposal,
            "high_impact": high_impact,
            "status": "scheduled",
            "contributions": [],
            "decision": None,
            "approval": None,
            "owner_approval": {"status": "not_required", "required_from": "André", "requested_at": None},
            "action_dispatch": {"status": "not_dispatched", "note": "No action is executed by the meeting registry."},
            "created_at": now,
            "updated_at": now,
            "history": [{"event": "meeting.created", "at": now, "actor": requested_by}],
        }
        with _LOCK:
            data = self._read()
            data["meetings"][meeting_id] = record
            self._write(data)
        return record

    def add_contribution(self, meeting_id: str, *, actor: str, content: str, kind: str = "contribution") -> dict[str, Any]:
        actor = _clean_text(actor, "actor", 120)
        content = _clean_text(content, "content")
        if kind not in {"contribution", "risk", "alternative", "evidence"}:
            raise ValueError("kind must be contribution, risk, alternative, or evidence")
        with _LOCK:
            data = self._read()
            meeting = data["meetings"].get(meeting_id)
            if meeting is None:
                raise KeyError(meeting_id)
            if meeting["status"] not in {"scheduled", "in_progress", "decision_pending"}:
                raise ValueError("contributions are not accepted after a final decision")
            now = _now()
            invalidated = meeting.get("decision") is not None
            meeting["contributions"].append({"contribution_id": str(uuid.uuid4()), "actor": actor, "kind": kind, "content": content, "created_at": now})
            if invalidated:
                meeting["decision"] = None
                meeting["approval"] = None
                meeting["owner_approval"] = {"status": "not_required", "required_from": "André", "requested_at": None}
                meeting["action_dispatch"] = {"status": "not_dispatched", "note": "New evidence invalidated the previous decision; a fresh decision and approval are required."}
                meeting["history"].append({"event": "meeting.plan_invalidated", "at": now, "actor": actor, "reason": "new_contribution"})
            meeting["status"] = "in_progress"
            meeting["updated_at"] = now
            meeting["history"].append({"event": "meeting.contribution_added", "at": now, "actor": actor})
            self._write(data)
            return meeting

    def record_decision(self, meeting_id: str, *, actor: str, outcome: str, rationale: str, action_plan: str = "") -> dict[str, Any]:
        actor = _clean_text(actor, "actor", 120)
        rationale = _clean_text(rationale, "rationale")
        if outcome not in {"approved", "rejected", "deferred"}:
            raise ValueError("outcome must be approved, rejected, or deferred")
        with _LOCK:
            data = self._read()
            meeting = data["meetings"].get(meeting_id)
            if meeting is None:
                raise KeyError(meeting_id)
            if meeting["status"] in {"approved", "rejected", "closed"}:
                raise ValueError("meeting already has a final state")
            now = _now()
            meeting["decision"] = {"outcome": outcome, "actor": actor, "rationale": rationale, "action_plan": action_plan.strip()[:4000], "created_at": now}
            meeting["decision"]["plan_digest"] = self._plan_digest(meeting)
            if outcome == "deferred":
                meeting["status"] = "decision_pending"
            elif meeting["high_impact"] and actor.casefold() not in {"ceo", "chief executive officer"}:
                meeting["status"] = "decision_pending"
                meeting["approval"] = {"status": "pending", "required_from": "CEO", "requested_at": now}
            elif outcome == "approved" and meeting["high_impact"]:
                meeting["status"] = "decision_pending"
                meeting["approval"] = {"status": "approved", "required_from": "CEO", "approved_by": actor, "decided_at": now}
                meeting["owner_approval"] = {"status": "pending", "required_from": "André", "requested_at": now}
                meeting["action_dispatch"] = {"status": "awaiting_owner_approval", "note": "CEO has prepared and endorsed the plan; no structural action may run before André's approval."}
            else:
                meeting["status"] = outcome
                meeting["approval"] = {"status": "not_required", "required_from": None, "requested_at": None}
            meeting["updated_at"] = now
            meeting["history"].append({"event": "meeting.decision_recorded", "at": now, "actor": actor, "outcome": outcome})
            self._write(data)
            return meeting

    def approve_decision(self, meeting_id: str, *, actor: str, approved: bool, rationale: str) -> dict[str, Any]:
        actor = _clean_text(actor, "actor", 120)
        rationale = _clean_text(rationale, "rationale")
        if actor.casefold() not in {"ceo", "chief executive officer"}:
            raise ValueError("only the CEO may approve a high-impact governance decision")
        with _LOCK:
            data = self._read()
            meeting = data["meetings"].get(meeting_id)
            if meeting is None:
                raise KeyError(meeting_id)
            if meeting["status"] != "decision_pending" or not meeting.get("approval") or meeting["approval"].get("status") != "pending":
                raise ValueError("there is no pending CEO approval")
            if not meeting.get("decision") or meeting["decision"].get("plan_digest") != self._plan_digest(meeting):
                raise ValueError("the reviewed plan changed; a fresh decision is required")
            now = _now()
            meeting["approval"] = {"status": "approved" if approved else "rejected", "actor": actor, "rationale": rationale, "decided_at": now, "plan_digest": meeting["decision"]["plan_digest"]}
            if approved:
                meeting["owner_approval"] = {"status": "pending", "required_from": "André", "requested_at": now}
                meeting["status"] = "decision_pending"
                meeting["action_dispatch"] = {"status": "awaiting_owner_approval", "note": "CEO endorsed the proposal; André's explicit approval is required before structural execution."}
            else:
                meeting["status"] = "rejected"
                meeting["owner_approval"] = {"status": "not_required", "required_from": "André", "requested_at": None}
                meeting["action_dispatch"] = {"status": "blocked", "note": "CEO rejected the decision."}
            meeting["updated_at"] = now
            meeting["history"].append({"event": "meeting.ceo_approval_recorded", "at": now, "actor": actor, "approved": approved})
            self._write(data)
            return meeting


    def approve_by_owner(self, meeting_id: str, *, actor: str, approved: bool, rationale: str) -> dict[str, Any]:
        """Record the human owner's final gate after the CEO has endorsed a critical plan."""
        actor = _clean_text(actor, "actor", 120)
        rationale = _clean_text(rationale, "rationale")
        if actor.casefold() not in {"andré", "andre", "owner", "system owner"}:
            raise ValueError("only the authenticated system owner may give the final approval")
        with _LOCK:
            data = self._read()
            meeting = data["meetings"].get(meeting_id)
            if meeting is None:
                raise KeyError(meeting_id)
            if meeting.get("owner_approval", {}).get("status") != "pending":
                raise ValueError("there is no pending owner approval")
            if meeting.get("approval", {}).get("status") != "approved":
                raise ValueError("CEO endorsement is required before owner approval")
            current_digest = self._plan_digest(meeting)
            if (
                not meeting.get("decision")
                or meeting["decision"].get("plan_digest") != current_digest
                or meeting["approval"].get("plan_digest") != current_digest
            ):
                raise ValueError("the reviewed plan changed; CEO and owner approval must be requested again")
            now = _now()
            meeting["owner_approval"] = {"status": "approved" if approved else "rejected", "actor": actor, "rationale": rationale, "decided_at": now, "plan_digest": current_digest}
            meeting["status"] = "approved" if approved else "rejected"
            meeting["updated_at"] = now
            meeting["history"].append({"event": "meeting.owner_approval_recorded", "at": now, "actor": actor, "approved": approved})
            meeting["action_dispatch"] = {"status": "ready_for_governed_execution", "note": "Human approval recorded. Execution must still use the governed action runner and verify the approved plan."} if approved else {"status": "blocked", "note": "André rejected the proposal."}
            self._write(data)
            return meeting
