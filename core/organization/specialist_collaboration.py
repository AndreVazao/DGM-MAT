"""Durable, zero-cost workflow for internal and external specialist collaboration.

This module prepares bounded work packets and records returned results. It does
not launch browsers, call models, consume credits, or authorize paid services.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import uuid4


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CollaborationStatus(str, Enum):
    PREPARED = "PREPARED"
    WAITING_FOR_FREE_CAPACITY = "WAITING_FOR_FREE_CAPACITY"
    RESULT_RECEIVED = "RESULT_RECEIVED"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"


class CollaborationSecurityError(ValueError):
    """Raised when a packet/result appears to contain authentication secrets."""


_SECRET_PATTERNS = (
    re.compile(r"(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|password|passwd|cookie|session[_-]?id)\s*[:=]\s*[^\s,;]{6,}"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bnvapi-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)


def _validate_text(value: str, field_name: str, *, required: bool = False, max_chars: int = 20000) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    value = value.strip()
    if required and not value:
        raise ValueError(f"{field_name} is required")
    if len(value) > max_chars:
        raise ValueError(f"{field_name} exceeds {max_chars} characters")
    for pattern in _SECRET_PATTERNS:
        if pattern.search(value):
            raise CollaborationSecurityError(
                f"{field_name} appears to contain a credential or session secret; remove it before saving"
            )
    return value


def _validate_lines(values: list[str] | tuple[str, ...], field_name: str) -> list[str]:
    if not isinstance(values, (list, tuple)):
        raise TypeError(f"{field_name} must be a list or tuple of strings")
    if len(values) > 100:
        raise ValueError(f"{field_name} contains too many items")
    return [_validate_text(item, field_name, required=True, max_chars=4000) for item in values]


@dataclass(slots=True)
class CollaborationPacket:
    collaboration_id: str
    goal: str
    project: str
    department: str
    specialist_role: str
    collaborator: str
    context: str = ""
    known_facts: list[str] = field(default_factory=list)
    attempted_steps: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    status: CollaborationStatus = CollaborationStatus.PREPARED
    blocked_reason: str | None = None
    result: str | None = None
    result_provenance: str | None = None
    review_notes: str | None = None
    reusable_lesson: str | None = None
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)


class SpecialistCollaborationStore:
    """Atomic local JSON ledger for specialist handoffs and validated learning."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()

    def _path(self, collaboration_id: str) -> Path:
        safe_id = _validate_text(collaboration_id, "collaboration_id", required=True, max_chars=128)
        if not re.fullmatch(r"[A-Za-z0-9_-]+", safe_id):
            raise ValueError("collaboration_id contains unsupported characters")
        return self.root / f"{safe_id}.json"

    def _write(self, packet: CollaborationPacket) -> None:
        path = self._path(packet.collaboration_id)
        payload = json.dumps(asdict(packet) | {"status": packet.status.value}, ensure_ascii=False, indent=2)
        fd, temp_name = tempfile.mkstemp(prefix=f".{packet.collaboration_id}.", suffix=".tmp", dir=self.root)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    def _read(self, collaboration_id: str) -> CollaborationPacket:
        path = self._path(collaboration_id)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise KeyError(collaboration_id) from exc
        data["status"] = CollaborationStatus(data["status"])
        return CollaborationPacket(**data)

    @staticmethod
    def _public_packet(packet: CollaborationPacket) -> dict[str, Any]:
        """Return the bounded handoff payload; never includes returned result or secrets."""
        return {
            "collaboration_id": packet.collaboration_id,
            "goal": packet.goal,
            "project": packet.project,
            "department": packet.department,
            "specialist_role": packet.specialist_role,
            "collaborator": packet.collaborator,
            "context": packet.context,
            "known_facts": list(packet.known_facts),
            "attempted_steps": list(packet.attempted_steps),
            "evidence": list(packet.evidence),
            "constraints": list(packet.constraints),
            "acceptance_criteria": list(packet.acceptance_criteria),
            "policy": {
                "mode": "FREE_ONLY",
                "paid_fallback": False,
                "external_call_authorized_by_packet": False,
                "instruction": "Perform only within the collaborator's legitimate free mode and terms. If limited, stop and return the limit state; do not upgrade, spend credits, or switch to a paid route.",
            },
        }

    def create_packet(
        self,
        *,
        goal: str,
        project: str,
        department: str,
        specialist_role: str,
        collaborator: str,
        context: str = "",
        known_facts: list[str] | tuple[str, ...] = (),
        attempted_steps: list[str] | tuple[str, ...] = (),
        evidence: list[str] | tuple[str, ...] = (),
        constraints: list[str] | tuple[str, ...] = (),
        acceptance_criteria: list[str] | tuple[str, ...] = (),
    ) -> dict[str, Any]:
        """Persist a handoff request and return the shareable task packet."""
        with self._lock:
            packet = CollaborationPacket(
                collaboration_id=f"collab_{uuid4().hex}",
                goal=_validate_text(goal, "goal", required=True, max_chars=4000),
                project=_validate_text(project, "project", required=True, max_chars=300),
                department=_validate_text(department, "department", required=True, max_chars=200),
                specialist_role=_validate_text(specialist_role, "specialist_role", required=True, max_chars=200),
                collaborator=_validate_text(collaborator, "collaborator", required=True, max_chars=200),
                context=_validate_text(context, "context", max_chars=20000),
                known_facts=_validate_lines(known_facts, "known_facts"),
                attempted_steps=_validate_lines(attempted_steps, "attempted_steps"),
                evidence=_validate_lines(evidence, "evidence"),
                constraints=_validate_lines(constraints, "constraints"),
                acceptance_criteria=_validate_lines(acceptance_criteria, "acceptance_criteria"),
            )
            self._write(packet)
            return self._public_packet(packet)

    def get(self, collaboration_id: str) -> CollaborationPacket:
        with self._lock:
            return self._read(collaboration_id)

    def list_packets(self) -> list[CollaborationPacket]:
        with self._lock:
            packets = [self._read(path.stem) for path in self.root.glob("collab_*.json")]
        return sorted(packets, key=lambda item: item.created_at)

    def mark_waiting_for_free_capacity(self, collaboration_id: str, *, reason: str) -> CollaborationPacket:
        """Pause handoff after a free-tier limit; never activate paid fallback."""
        with self._lock:
            packet = self._read(collaboration_id)
            if packet.status in {CollaborationStatus.VALIDATED, CollaborationStatus.REJECTED}:
                raise ValueError(f"Cannot pause a terminal collaboration: {packet.status.value}")
            packet.status = CollaborationStatus.WAITING_FOR_FREE_CAPACITY
            packet.blocked_reason = _validate_text(reason, "reason", required=True, max_chars=2000)
            packet.updated_at = _now()
            self._write(packet)
            return packet

    def record_result(
        self,
        collaboration_id: str,
        *,
        result: str,
        provenance: str,
    ) -> CollaborationPacket:
        """Store an external/local specialist response for review, not as trusted truth."""
        with self._lock:
            packet = self._read(collaboration_id)
            if packet.status in {CollaborationStatus.VALIDATED, CollaborationStatus.REJECTED}:
                raise ValueError(f"Cannot add a result to a terminal collaboration: {packet.status.value}")
            packet.result = _validate_text(result, "result", required=True, max_chars=50000)
            packet.result_provenance = _validate_text(provenance, "provenance", required=True, max_chars=2000)
            packet.review_notes = None
            packet.reusable_lesson = None
            packet.status = CollaborationStatus.RESULT_RECEIVED
            packet.blocked_reason = None
            packet.updated_at = _now()
            self._write(packet)
            return packet

    def validate_result(
        self,
        collaboration_id: str,
        *,
        reviewer: str,
        review_notes: str,
        evidence: list[str] | tuple[str, ...],
        tests_passed: bool,
        reusable_lesson: str,
    ) -> CollaborationPacket:
        """Promote a lesson only after explicit independent review and passing tests."""
        with self._lock:
            packet = self._read(collaboration_id)
            if packet.status != CollaborationStatus.RESULT_RECEIVED or packet.result is None:
                raise ValueError("A received result is required before review")
            if type(tests_passed) is not bool or not tests_passed:
                raise ValueError("Result cannot be validated unless tests_passed is exactly True")
            reviewer = _validate_text(reviewer, "reviewer", required=True, max_chars=200)
            if reviewer.lower() in {packet.collaborator.lower(), "self", "same-provider"}:
                raise ValueError("Independent reviewer must differ from the original collaborator")
            review_notes = _validate_text(review_notes, "review_notes", required=True, max_chars=8000)
            review_evidence = _validate_lines(evidence, "review evidence")
            if not review_evidence:
                raise ValueError("Independent review evidence is required")
            lesson = _validate_text(reusable_lesson, "reusable_lesson", required=True, max_chars=8000)
            packet.review_notes = f"Reviewer: {reviewer}\n{review_notes}\nEvidence: " + "; ".join(review_evidence)
            packet.reusable_lesson = lesson
            packet.status = CollaborationStatus.VALIDATED
            packet.updated_at = _now()
            self._write(packet)
            return packet

    def reject_result(self, collaboration_id: str, *, reviewer: str, reason: str) -> CollaborationPacket:
        with self._lock:
            packet = self._read(collaboration_id)
            if packet.status != CollaborationStatus.RESULT_RECEIVED:
                raise ValueError("Only a received result can be rejected")
            reviewer = _validate_text(reviewer, "reviewer", required=True, max_chars=200)
            if reviewer.lower() in {packet.collaborator.lower(), "self", "same-provider"}:
                raise ValueError("Independent reviewer must differ from the original collaborator")
            packet.review_notes = f"Rejected by {reviewer}: " + _validate_text(reason, "reason", required=True, max_chars=8000)
            packet.reusable_lesson = None
            packet.status = CollaborationStatus.REJECTED
            packet.updated_at = _now()
            self._write(packet)
            return packet
