"""Durable, privacy-minimized observations from completed mission execution.

Observations are not promoted lessons. Reusable lessons must still pass the
independent validation workflow in core.organization.validated_learning.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import uuid4

from core.storage.storage_manager import storage_manager


class LearningEngine:
    """Persist structured execution observations without storing raw prompts/errors."""

    def __init__(self, observations_path: str | Path | None = None) -> None:
        self.observations_path = (
            Path(observations_path).expanduser().resolve()
            if observations_path is not None
            else storage_manager.get_path("patterns", "execution_observations.jsonl")
        )
        self.observations_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self.learnings: list[dict[str, Any]] = self._load_observations()

    def _load_observations(self) -> list[dict[str, Any]]:
        if not self.observations_path.exists():
            return []
        observations: list[dict[str, Any]] = []
        try:
            for line in self.observations_path.read_text(encoding="utf-8").splitlines():
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(record, dict) and record.get("schema") == "dgm.execution-observation.v1":
                    observations.append(record)
        except OSError:
            # Keep the engine usable for diagnostics; writes will report their own failure.
            return []
        return observations[-1000:]

    @staticmethod
    def _safe_label(value: Any, fallback: str = "unknown") -> str:
        if not isinstance(value, str):
            return fallback
        normalized = re.sub(r"[^A-Za-z0-9_.:-]+", "_", value.strip())
        return normalized[:120] or fallback

    def learn_from_execution(self, execution_data: dict[str, Any]) -> dict[str, Any]:
        """Record a durable outcome observation; do not claim model training or lesson promotion."""
        if not isinstance(execution_data, dict):
            raise TypeError("execution_data must be a dictionary")

        status = self._safe_label(execution_data.get("status"), "UNKNOWN").upper()
        success_value = execution_data.get("success")
        success = bool(success_value) if success_value is not None else status in {"COMPLETED", "SUCCESS"}
        handler = self._safe_label(execution_data.get("handler"))
        error_type = self._safe_label(execution_data.get("error_type"), "none") if not success else "none"
        mission_id = self._safe_label(execution_data.get("mission_id"), "unknown")
        try:
            duration = max(0.0, min(float(execution_data.get("duration_seconds", 0.0)), 86400.0))
        except (TypeError, ValueError):
            duration = 0.0

        pattern_material = json.dumps(
            {"handler": handler, "status": status, "error_type": error_type},
            sort_keys=True,
            separators=(",", ":"),
        )
        pattern_id = hashlib.sha256(pattern_material.encode("utf-8")).hexdigest()[:16]
        record = {
            "schema": "dgm.execution-observation.v1",
            "observation_id": f"observation_{uuid4().hex}",
            "mission_id": mission_id,
            "handler": handler,
            "status": status,
            "success": success,
            "error_type": error_type,
            "duration_seconds": round(duration, 3),
            "pattern_id": pattern_id,
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "promotion_status": "OBSERVATION_ONLY",
        }

        line = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
        with self._lock:
            with self.observations_path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(line + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            self.learnings.append(record)
            if len(self.learnings) > 1000:
                self.learnings = self.learnings[-1000:]
        return record

    def summarize(self) -> dict[str, Any]:
        successful = sum(1 for item in self.learnings if item.get("success") is True)
        failed = sum(1 for item in self.learnings if item.get("success") is False)
        return {
            "observations": len(self.learnings),
            "successful": successful,
            "failed": failed,
            "unique_patterns": len({item.get("pattern_id") for item in self.learnings}),
            "lesson_promotion": "requires independent validation",
        }
