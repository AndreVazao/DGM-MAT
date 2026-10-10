"""Explicit, policy-bounded dispatch of durable internal agent messages.

This runtime executes only Python handlers registered by the host application.
It never interprets message bodies as code, shell commands, or tool instructions.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any

from .message_bus import InternalMessageBus
from .models import Message


MessageHandler = Callable[[Message], Any]


@dataclass(frozen=True, slots=True)
class DispatchResult:
    agent_id: str
    message_id: str
    status: str
    result: Any = None
    error_type: str | None = None


class WorkerRuntime:
    """Dispatch unread messages to an explicitly registered handler per agent."""

    def __init__(self, bus: InternalMessageBus) -> None:
        self.bus = bus
        self._handlers: dict[str, MessageHandler] = {}

    def register_handler(self, agent_id: str, handler: MessageHandler) -> None:
        if not isinstance(agent_id, str) or not agent_id.strip():
            raise ValueError("agent_id is required")
        if not callable(handler):
            raise TypeError("handler must be callable")
        if agent_id in self._handlers:
            raise ValueError(f"Handler already registered for {agent_id}")
        self._handlers[agent_id] = handler

    def dispatch_one(self, agent_id: str) -> DispatchResult | None:
        handler = self._handlers.get(agent_id)
        if handler is None:
            raise KeyError(f"No explicit worker handler registered for {agent_id}")
        messages = self.bus.receive(agent_id, unread_only=True)
        if not messages:
            return None
        message = messages[0]
        try:
            result = handler(message)
        except Exception as exc:
            # Leave unread so a supervisor can inspect/retry; never hide failure.
            return DispatchResult(
                agent_id=agent_id,
                message_id=message.message_id,
                status="HANDLER_FAILED_UNACKNOWLEDGED",
                error_type=type(exc).__name__,
            )
        self.bus.mark_read(agent_id, message.message_id)
        return DispatchResult(
            agent_id=agent_id,
            message_id=message.message_id,
            status="HANDLED",
            result=result,
        )
