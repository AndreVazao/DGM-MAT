# Path: C:\ProgramasGodMode\DGM-MAT\core\mobile_runtime\store.py
from __future__ import annotations

import json
import os
import threading
import uuid
from pathlib import Path
from typing import Any

from .models import ConversationMessage, ConversationThread, utc_now


class ConversationStore:
    """Small, durable, atomic JSON store optimized for the old 3 GB PC."""

    def __init__(self, path: str | Path | None = None) -> None:
        if path is None:
            base = Path(os.getenv("DGM_STORAGE_PATH", "C:/ProgramasGodMode/DGM-MAT/storage/runtime"))
            path = base / "sessions" / "mobile_conversations.json"
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._threads: dict[str, ConversationThread] = {}
        self._load()

    def _load(self) -> None:
        with self._lock:
            if not self.path.exists():
                return
            try:
                payload = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                return
            for item in payload.get("threads", []):
                try:
                    messages = [
                        ConversationMessage(**message)
                        for message in item.get("messages", [])
                    ]
                    thread = ConversationThread(
                        id=item["id"],
                        title=item.get("title") or "Nova conversa",
                        created_at=item.get("created_at") or utc_now(),
                        updated_at=item.get("updated_at") or utc_now(),
                        project=item.get("project"),
                        repository=item.get("repository"),
                        status=item.get("status", "active"),
                        messages=messages,
                        context=item.get("context", {}),
                    )
                    self._threads[thread.id] = thread
                except (KeyError, TypeError):
                    continue

    def _save(self) -> None:
        payload = {
            "schema": "dgm-mat.mobile-conversations.v1",
            "updated_at": utc_now(),
            "threads": [thread.to_dict() for thread in self._threads.values()],
        }
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(self.path)

    def list_threads(self) -> list[ConversationThread]:
        with self._lock:
            return sorted(
                self._threads.values(),
                key=lambda item: item.updated_at,
                reverse=True,
            )

    def create_thread(
        self,
        title: str = "Nova conversa",
        project: str | None = None,
        repository: str | None = None,
    ) -> ConversationThread:
        with self._lock:
            now = utc_now()
            thread = ConversationThread(
                id=f"thread-{uuid.uuid4().hex[:16]}",
                title=title.strip() or "Nova conversa",
                created_at=now,
                updated_at=now,
                project=project,
                repository=repository,
            )
            self._threads[thread.id] = thread
            self._save()
            return thread

    def get_thread(self, thread_id: str) -> ConversationThread | None:
        with self._lock:
            return self._threads.get(thread_id)

    def append_message(
        self,
        thread_id: str,
        role: str,
        content: str,
        state: str = "ready",
        metadata: dict[str, Any] | None = None,
    ) -> ConversationMessage:
        with self._lock:
            thread = self._threads[thread_id]
            message = ConversationMessage(
                id=f"msg-{uuid.uuid4().hex[:16]}",
                role=role,
                content=content,
                state=state,
                metadata=metadata or {},
            )
            thread.messages.append(message)
            thread.updated_at = utc_now()
            self._save()
            return message

    def rename(self, thread_id: str, title: str) -> ConversationThread:
        with self._lock:
            thread = self._threads[thread_id]
            thread.title = title.strip() or thread.title
            thread.updated_at = utc_now()
            self._save()
            return thread

    def update_context(
        self,
        thread_id: str,
        *,
        project: str | None = None,
        repository: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> ConversationThread:
        with self._lock:
            thread = self._threads[thread_id]
            if project is not None:
                thread.project = project
            if repository is not None:
                thread.repository = repository
            if context:
                thread.context.update(context)
            thread.updated_at = utc_now()
            self._save()
            return thread
