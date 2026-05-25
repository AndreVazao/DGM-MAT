import json
import time
import os
from typing import Dict, Any, List, Optional
from core.storage.storage_manager import storage_manager
from core.observability.logger import dgm_logger

class JournalEntry:
    def __init__(self, id: str, action: str, reasoning: str, status: str, payload: Dict[str, Any] = None, result: Dict[str, Any] = None):
        self.id = id
        self.timestamp = time.time()
        self.action = action
        self.reasoning = reasoning
        self.status = status
        self.payload = payload or {}
        self.result = result or {}

    def to_dict(self):
        return self.__dict__

class ExecutionJournal:
    """
    Persistent journal for tracking autonomous decisions and actions.
    """
    def __init__(self):
        self.storage_path = storage_manager.get_path("logs", "execution_journal.jsonl")
        self._ensure_storage()

    def _ensure_storage(self):
        if not self.storage_path.parent.exists():
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def log_action(self, action: str, reasoning: str, payload: Dict[str, Any] = None) -> str:
        entry_id = f"journal_{int(time.time())}_{os.urandom(4).hex()}"
        entry = JournalEntry(id=entry_id, action=action, reasoning=reasoning, status="started", payload=payload)
        self._write_entry(entry)
        dgm_logger.info(f"Journal: Logged action {action} ({entry_id})")
        return entry_id

    def update_action(self, entry_id: str, status: str, result: Dict[str, Any] = None):
        # In a real implementation, we'd probably append a new entry or update a database.
        # For simplicity in this local-first version, we'll append an 'update' record.
        entry = JournalEntry(id=entry_id, action="UPDATE", reasoning="", status=status, result=result)
        self._write_entry(entry)
        dgm_logger.info(f"Journal: Updated action {entry_id} to {status}")

    def _write_entry(self, entry: JournalEntry):
        try:
            with open(self.storage_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry.to_dict()) + "\n")
        except Exception as e:
            dgm_logger.error(f"Journal: Failed to write entry: {e}")

    def health(self) -> Dict[str, Any]:
        return {
            "journal_file": str(self.storage_path),
            "exists": self.storage_path.exists()
        }

    def metrics(self) -> Dict[str, Any]:
        count = 0
        if self.storage_path.exists():
            with open(self.storage_path, "r") as f:
                count = sum(1 for _ in f)
        return {
            "total_entries": count
        }
