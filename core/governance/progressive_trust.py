"""Evidence-based, scoped progressive-trust policy for CEO decisions.

This module records feedback and evaluates existing owner-granted delegations.
It never grants authority automatically and never executes actions.
"""
from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_LOCK = threading.RLock()
_RISK_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}
_PROTECTED_BOUNDARIES = {
    "security_boundary", "credential_access", "sensitive_data",
    "irreversible_change", "unapproved_spend", "major_architecture",
    "cross_department_reorganization", "legal_or_compliance",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _required(value: str, field: str, limit: int = 200) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    value = value.strip()
    if len(value) > limit:
        raise ValueError(f"{field} exceeds {limit} characters")
    return value


class ProgressiveTrustRegistry:
    """Durable feedback log and owner-controlled, scope-limited delegation registry."""

    def __init__(self, path: str | Path | None = None):
        configured = path or os.environ.get("DGM_PROGRESSIVE_TRUST_PATH")
        self.path = Path(configured) if configured else Path("data/governance/progressive_trust.json")

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema_version": 1, "feedback": [], "delegations": []}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError("Progressive-trust store is unreadable; refusing to overwrite it.") from exc
        if (
            not isinstance(data, dict)
            or data.get("schema_version") != 1
            or not isinstance(data.get("feedback"), list)
            or not isinstance(data.get("delegations"), list)
        ):
            raise RuntimeError("Progressive-trust store has an unsupported schema; refusing to overwrite it.")
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

    def record_feedback(
        self, *, category: str, scope: str, outcome: str, rationale: str,
        risk: str, reversible: bool, verified_success: bool = False,
    ) -> dict[str, Any]:
        category = _required(category, "category").casefold()
        scope = _required(scope, "scope").casefold()
        rationale = _required(rationale, "rationale", 2000)
        if outcome not in {"approved", "rejected", "changed", "revoked"}:
            raise ValueError("outcome must be approved, rejected, changed, or revoked")
        if risk not in _RISK_ORDER:
            raise ValueError("risk must be low, medium, high, or critical")
        if verified_success and outcome != "approved":
            raise ValueError("verified_success is valid only for approved decisions")
        item = {
            "feedback_id": str(uuid.uuid4()), "category": category, "scope": scope,
            "outcome": outcome, "rationale": rationale, "risk": risk,
            "reversible": bool(reversible), "verified_success": bool(verified_success),
            "created_at": _now(),
        }
        with _LOCK:
            data = self._read()
            data["feedback"].append(item)
            self._write(data)
        return item

    def grant_delegation(
        self, *, actor: str, category: str, scope: str, max_risk: str,
        min_verified_successes: int = 3, rationale: str,
        protected_boundaries: list[str] | None = None,
    ) -> dict[str, Any]:
        """Only an authenticated owner identity passed by a trusted caller can grant scope."""
        actor = _required(actor, "actor").casefold()
        if actor not in {"andre", "andré", "andrevazao", "owner", "system owner"}:
            raise ValueError("only the system owner may grant or expand decision authority")
        category = _required(category, "category").casefold()
        scope = _required(scope, "scope").casefold()
        rationale = _required(rationale, "rationale", 2000)
        if max_risk not in {"low", "medium"}:
            raise ValueError("progressive delegation is limited to low or medium risk")
        if not isinstance(min_verified_successes, int) or not 3 <= min_verified_successes <= 20:
            raise ValueError("min_verified_successes must be between 3 and 20")
        boundaries = sorted(set(protected_boundaries or _PROTECTED_BOUNDARIES))
        if not set(boundaries).issuperset(_PROTECTED_BOUNDARIES):
            raise ValueError("delegation must retain every mandatory protected boundary")
        item = {
            "delegation_id": str(uuid.uuid4()), "category": category, "scope": scope,
            "max_risk": max_risk, "min_verified_successes": min_verified_successes,
            "protected_boundaries": boundaries, "rationale": rationale,
            "granted_by": actor, "created_at": _now(), "active": True,
        }
        with _LOCK:
            data = self._read()
            data["delegations"].append(item)
            self._write(data)
        return item

    def revoke_delegation(self, *, actor: str, delegation_id: str, rationale: str) -> dict[str, Any]:
        actor = _required(actor, "actor").casefold()
        if actor not in {"andre", "andré", "andrevazao", "owner", "system owner"}:
            raise ValueError("only the system owner may revoke decision authority")
        rationale = _required(rationale, "rationale", 2000)
        with _LOCK:
            data = self._read()
            item = next((d for d in data["delegations"] if d["delegation_id"] == delegation_id), None)
            if item is None:
                raise KeyError(delegation_id)
            item["active"] = False
            item["revoked_at"] = _now()
            item["revoked_by"] = actor
            item["revocation_rationale"] = rationale
            self._write(data)
            return item

    def evaluate(
        self, *, category: str, scope: str, risk: str,
        protected_boundaries: list[str] | None = None, materially_changed: bool = False,
    ) -> dict[str, Any]:
        """Evaluate an action against existing delegations; never creates authority."""
        category = _required(category, "category").casefold()
        scope = _required(scope, "scope").casefold()
        if risk not in _RISK_ORDER:
            raise ValueError("risk must be low, medium, high, or critical")
        boundaries = set(protected_boundaries or [])
        with _LOCK:
            data = self._read()
        matched = [
            d for d in data["delegations"]
            if d.get("active") is True and d.get("category") == category and d.get("scope") == scope
        ]
        reasons: list[str] = []
        if materially_changed:
            reasons.append("Plan or circumstances materially changed; prior trust cannot be reused.")
        if boundaries & _PROTECTED_BOUNDARIES:
            reasons.append("Action crosses a mandatory protected boundary.")
        if not matched:
            reasons.append("No active owner-granted delegation matches this exact category and scope.")
        eligible = False
        evidence_count = 0
        if matched and not materially_changed and not (boundaries & _PROTECTED_BOUNDARIES):
            delegation = matched[-1]
            if _RISK_ORDER[risk] > _RISK_ORDER[delegation["max_risk"]]:
                reasons.append("Risk exceeds the delegated maximum.")
            else:
                feedback = [
                    f for f in data["feedback"]
                    if f["category"] == category and f["scope"] == scope
                ]
                # Count verified successes since the most recent negative correction.
                last_negative = max(
                    (i for i, f in enumerate(feedback) if f["outcome"] in {"rejected", "changed", "revoked"}),
                    default=-1,
                )
                evidence_count = sum(
                    1 for f in feedback[last_negative + 1:]
                    if f["outcome"] == "approved" and f["verified_success"]
                    and f["reversible"] and _RISK_ORDER[f["risk"]] <= _RISK_ORDER[delegation["max_risk"]]
                )
                if evidence_count < delegation["min_verified_successes"]:
                    reasons.append(
                        f"Insufficient verified pattern: {evidence_count}/{delegation['min_verified_successes']} required successes."
                    )
                else:
                    eligible = True
                    reasons.append("Existing owner-granted delegation and verified evidence match this bounded action.")
        return {
            "autonomous_decision_allowed": eligible,
            "category": category, "scope": scope, "risk": risk,
            "verified_successes": evidence_count,
            "matched_delegation_id": matched[-1]["delegation_id"] if matched else None,
            "reasons": reasons,
            "execution_permitted": False,
            "note": "This is a decision-policy result only; execution requires the separate governed action runner.",
        }
