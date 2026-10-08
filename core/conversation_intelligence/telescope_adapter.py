from __future__ import annotations

import json
import shutil
import subprocess

from .models import ConversationRecord


class TelescopeAdapter:
    """Read Telescope machine-readable session data when installed."""

    def __init__(self, executable: str = "tele"):
        self.executable = executable

    def available(self) -> bool:
        return shutil.which(self.executable) is not None

    def sessions(self) -> list[dict]:
        if not self.available():
            return []
        result = subprocess.run([self.executable, "sessions", "list", "--json"], capture_output=True, text=True, timeout=15, check=False)
        if result.returncode != 0 or not result.stdout.strip():
            return []
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            return []
        return data if isinstance(data, list) else data.get("sessions", [])

    def conversation(self, session_id: str) -> ConversationRecord | None:
        if not self.available():
            return None
        result = subprocess.run([self.executable, "sessions", "get", session_id, "--json"], capture_output=True, text=True, timeout=15, check=False)
        if result.returncode != 0 or not result.stdout.strip():
            return None
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            return None
        title = str(data.get("title") or data.get("name") or session_id)
        content = json.dumps(data, ensure_ascii=False, indent=2)
        return ConversationRecord(session_id, "telescope", title, content, "telescope", metadata={"session": data})
