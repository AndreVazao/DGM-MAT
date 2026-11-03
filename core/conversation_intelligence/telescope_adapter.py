from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import PurePath
from typing import Any

from .models import ConversationRecord


class TelescopeAdapter:
    """Read Telescope session metadata without importing prompts or responses.

    Telescope's `sessions get` payload can contain full turns and last-message
    previews. This adapter deliberately projects it onto a small allowlist.
    """

    _METADATA_FIELDS = (
        "session_id",
        "agent_id",
        "git_branch",
        "status",
        "started_at",
        "ended_at",
        "turn_count",
        "duration_ms",
    )

    def __init__(self, executable: str = "tele", timeout: float = 15):
        self.executable = executable
        self.timeout = timeout

    def available(self) -> bool:
        return shutil.which(self.executable) is not None

    @staticmethod
    def _project_name(value: Any) -> str | None:
        """Keep only the final directory name; never persist an absolute path."""
        if not isinstance(value, str) or not value.strip():
            return None
        normalized = value.replace("\\", "/").rstrip("/")
        name = PurePath(normalized).name
        return name[:160] if name and name not in {".", ".."} else None

    @classmethod
    def _safe_metadata(cls, data: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            return {}
        safe = {
            key: data[key]
            for key in cls._METADATA_FIELDS
            if key in data and isinstance(data[key], (str, int, float, bool, type(None)))
        }
        project = cls._project_name(data.get("cwd"))
        if project:
            safe["project"] = project
        return safe

    def _run_json(self, *arguments: str) -> Any:
        if not self.available():
            return None
        try:
            result = subprocess.run(
                [self.executable, *arguments],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if result.returncode != 0 or not result.stdout.strip():
            return None
        try:
            return json.loads(result.stdout)
        except (json.JSONDecodeError, TypeError):
            return None

    def sessions(self) -> list[dict[str, Any]]:
        """Return safe session metadata only; never return raw Telescope objects."""
        data = self._run_json("sessions", "list", "--json")
        items = data if isinstance(data, list) else data.get("sessions", []) if isinstance(data, dict) else []
        return [self._safe_metadata(item) for item in items if isinstance(item, dict)]

    def conversation(self, session_id: str) -> ConversationRecord | None:
        """Build a metadata record from the list endpoint; never fetch session details."""
        if not isinstance(session_id, str) or not session_id.strip() or len(session_id) > 256:
            return None
        safe = next(
            (item for item in self.sessions() if item.get("session_id") == session_id),
            None,
        )
        if safe is None:
            return None
        title = f"Telescope session {session_id[:12]}"
        content = json.dumps(safe, ensure_ascii=False, indent=2, sort_keys=True)
        return ConversationRecord(
            conversation_id=session_id,
            provider="telescope",
            title=title,
            content=content,
            source="telescope-metadata",
            metadata={"session": safe, "content_policy": "metadata_only"},
        )
