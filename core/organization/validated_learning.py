"""Persistent project-scoped lessons promoted only from validated collaborations.

This store does not decide whether a result is correct. Callers must first use
SpecialistCollaborationStore.validate_result with independent review and test
evidence. Only packets already marked VALIDATED can be recorded here.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

from .specialist_collaboration import CollaborationPacket, CollaborationStatus


class ValidatedLessonStore:
    """Atomic local JSON store for independently reviewed reusable lessons."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()

    @staticmethod
    def _safe_id(value: str) -> str:
        if not isinstance(value, str) or not re.fullmatch(r"collab_[A-Za-z0-9_-]+", value):
            raise ValueError("Invalid collaboration ID for validated lesson")
        return value

    def record(self, packet: CollaborationPacket) -> dict[str, Any]:
        if packet.status != CollaborationStatus.VALIDATED:
            raise ValueError("Only a VALIDATED collaboration can become a reusable lesson")
        if not packet.reusable_lesson or not packet.review_notes or not packet.result_provenance:
            raise ValueError("Validated collaboration is missing lesson, review, or provenance")
        collaboration_id = self._safe_id(packet.collaboration_id)
        record = {
            "lesson_id": f"lesson_{collaboration_id}",
            "collaboration_id": collaboration_id,
            "scope": "project",
            "project": packet.project,
            "department": packet.department,
            "specialist_role": packet.specialist_role,
            "source_collaborator": packet.collaborator,
            "source_provenance": packet.result_provenance,
            "lesson": packet.reusable_lesson,
            "review_notes": packet.review_notes,
            "acceptance_criteria": list(packet.acceptance_criteria),
            "status": "VALIDATED",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        destination = self.root / f"{collaboration_id}.json"
        with self._lock:
            fd, temporary = tempfile.mkstemp(prefix=f".{collaboration_id}.", suffix=".tmp", dir=self.root)
            try:
                with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                    json.dump(record, handle, ensure_ascii=False, indent=2)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, destination)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
        return record

    def get(self, collaboration_id: str) -> dict[str, Any]:
        safe_id = self._safe_id(collaboration_id)
        path = self.root / f"{safe_id}.json"
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise KeyError(collaboration_id) from exc
        if record.get("status") != "VALIDATED":
            raise ValueError("Stored lesson is not validated")
        return record

    def list_lessons(self, *, project: str | None = None) -> list[dict[str, Any]]:
        lessons = []
        with self._lock:
            for path in self.root.glob("collab_*.json"):
                try:
                    record = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                if record.get("status") != "VALIDATED":
                    continue
                if project is not None and record.get("project") != project:
                    continue
                lessons.append(record)
        return sorted(lessons, key=lambda item: item.get("created_at", ""))
