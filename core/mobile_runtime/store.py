# Path: C:\ProgramasGodMode\DGM-MAT\core\mobile_runtime\store.py
from __future__ import annotations

import json
import threading
import uuid
from pathlib import Path
from typing import Any

from .models import ConversationMessage, ConversationThread, utc_now
from core.storage.storage_manager import storage_manager


class ConversationStore:
    """Small, durable, atomic JSON store optimized for the old 3 GB PC."""

    def __init__(self, path: str | Path | None = None) -> None:
        if path is None:
            path = storage_manager.get_path("sessions", "mobile_conversations.json")
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

    def search_threads_page(
        self,
        query: str,
        limit: int = 25,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Return a deterministic, bounded page of local threads matching metadata or message text."""
        needle = query.strip().casefold()
        if len(needle) < 2:
            return {"results": [], "total_count": 0, "limit": max(1, min(int(limit), 50)), "offset": max(0, int(offset)), "has_more": False}
        bounded_limit = max(1, min(int(limit), 50))
        bounded_offset = max(0, int(offset))
        with self._lock:
            ordered = sorted(
                self._threads.values(),
                key=lambda item: (item.updated_at, item.id),
                reverse=True,
            )
            matches: list[dict[str, Any]] = []
            for thread in ordered:
                title_match = needle in (thread.title or "").casefold()
                context_match = needle in " ".join(
                    value for value in (thread.project, thread.repository) if isinstance(value, str)
                ).casefold()
                matched_message = None
                if not title_match and not context_match:
                    for message in reversed(thread.messages):
                        content = message.content if isinstance(message.content, str) else ""
                        position = content.casefold().find(needle)
                        if position < 0:
                            continue
                        start = max(0, position - 100)
                        end = min(len(content), position + len(needle) + 160)
                        matched_message = {
                            "message_id": message.id,
                            "message_role": message.role,
                            "message_created_at": message.created_at,
                            "snippet": content[start:end],
                        }
                        break
                if not title_match and not context_match and matched_message is None:
                    continue
                result: dict[str, Any] = {
                    "thread_id": thread.id,
                    "title": thread.title,
                    "created_at": thread.created_at,
                    "updated_at": thread.updated_at,
                    "project": thread.project,
                    "repository": thread.repository,
                    "match_type": "title" if title_match else "context" if context_match else "message",
                    "provenance": {
                        "source": "dgm-mat-local-conversation-store",
                        "thread_id": thread.id,
                        "capture_completeness": "complete",
                    },
                }
                if matched_message:
                    result.update(matched_message)
                else:
                    result["snippet"] = (thread.title or "Nova conversa")[:240]
                matches.append(result)

            total_count = len(matches)
            results = matches[bounded_offset:bounded_offset + bounded_limit]
            next_offset = bounded_offset + len(results)
            return {
                "results": results,
                "total_count": total_count,
                "limit": bounded_limit,
                "offset": bounded_offset,
                "next_offset": next_offset if next_offset < total_count else None,
                "has_more": next_offset < total_count,
            }

    def search_threads(self, query: str, limit: int = 25, offset: int = 0) -> list[dict[str, Any]]:
        """Backward-compatible list interface for existing callers."""
        return self.search_threads_page(query, limit=limit, offset=offset)["results"]

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

    def set_status(self, thread_id: str, status: str) -> ConversationThread:
        """Archive or restore a thread without deleting its messages."""
        normalized = str(status).strip().casefold()
        if normalized not in {"active", "archived"}:
            raise ValueError("status must be active or archived")
        with self._lock:
            thread = self._threads[thread_id]
            thread.status = normalized
            thread.updated_at = utc_now()
            self._save()
            return thread

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
