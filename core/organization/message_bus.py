"""Internal communication bus for DGM-MAT digital employees."""

from __future__ import annotations

from collections import defaultdict
from threading import RLock

from .models import Message, MessagePriority


class InternalMessageBus:
    """In-process message bus with durable-friendly message semantics.

    The first implementation keeps messages in memory and exposes explicit
    inbox/outbox operations. Persistence can later be backed by EventStore
    without changing the agent-facing contract.
    """

    def __init__(self) -> None:
        self._inboxes: dict[str, list[Message]] = defaultdict(list)
        self._outboxes: dict[str, list[Message]] = defaultdict(list)
        self._lock = RLock()

    def send(self, message: Message) -> str:
        with self._lock:
            self._outboxes[message.sender_id].append(message)
            self._inboxes[message.recipient_id].append(message)
        return message.message_id

    def receive(
        self,
        agent_id: str,
        *,
        priority: MessagePriority | None = None,
        unread_only: bool = False,
    ) -> list[Message]:
        with self._lock:
            messages = list(self._inboxes.get(agent_id, []))
        if priority is not None:
            messages = [m for m in messages if m.priority == priority]
        if unread_only:
            messages = [m for m in messages if m.read_at is None]
        return messages

    def mark_read(self, agent_id: str, message_id: str) -> None:
        with self._lock:
            for message in self._inboxes.get(agent_id, []):
                if message.message_id == message_id:
                    from .models import utc_now
                    message.read_at = utc_now()
                    return
        raise KeyError(message_id)

    def outbox(self, agent_id: str) -> list[Message]:
        with self._lock:
            return list(self._outboxes.get(agent_id, []))

    def counts(self) -> dict[str, int]:
        with self._lock:
            return {
                "inboxes": sum(len(v) for v in self._inboxes.values()),
                "outboxes": sum(len(v) for v in self._outboxes.values()),
            }
