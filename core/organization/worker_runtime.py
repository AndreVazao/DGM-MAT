"""Explicit, policy-bounded dispatch of durable internal agent messages.

This runtime executes only Python handlers registered by the host application.
It never interprets message bodies as code, shell commands, or tool instructions.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any, Iterable

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
        self._handler_capabilities: dict[str, frozenset[str]] = {}

    def register_handler(
        self,
        agent_id: str,
        handler: MessageHandler,
        *,
        capabilities: Iterable[str] | None = None,
    ) -> None:
        if not isinstance(agent_id, str) or not agent_id.strip():
            raise ValueError("agent_id is required")
        if not callable(handler):
            raise TypeError("handler must be callable")
        if agent_id in self._handlers:
            raise ValueError(f"Handler already registered for {agent_id}")
        declared = getattr(handler, "capabilities", ()) if capabilities is None else capabilities
        if isinstance(declared, (str, bytes)) or not isinstance(declared, Iterable):
            raise TypeError("handler capabilities must be an iterable of strings")
        normalized: set[str] = set()
        for capability in declared:
            if not isinstance(capability, str) or not capability.strip():
                raise ValueError("handler capabilities must contain non-empty strings")
            normalized.add(capability.strip().casefold())
        self._handlers[agent_id] = handler
        self._handler_capabilities[agent_id] = frozenset(normalized)

    def has_handler(self, agent_id: str) -> bool:
        """Return whether this runtime has an explicit handler for the agent."""
        return agent_id in self._handlers

    def registered_agents(self) -> tuple[str, ...]:
        """Return stable IDs of explicitly registered handlers."""
        return tuple(sorted(self._handlers))

    def declared_capabilities(self, agent_id: str) -> tuple[str, ...]:
        """Return capabilities explicitly declared by a registered handler."""
        return tuple(sorted(self._handler_capabilities.get(agent_id, frozenset())))

    def declares_capabilities(self, agent_id: str, required: Iterable[str]) -> bool:
        """Check handler declarations; this is not proof of task-level validation."""
        if not self.has_handler(agent_id):
            return False
        required_set = {
            item.strip().casefold()
            for item in required
            if isinstance(item, str) and item.strip()
        }
        return required_set.issubset(self._handler_capabilities.get(agent_id, frozenset()))

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
            # Persist result and acknowledgement in one SQLite transaction.
            self.bus.complete_dispatch(agent_id, message.message_id, result)
        except Exception as exc:
            # Leave unread so a supervisor can inspect/retry; never hide failure.
            return DispatchResult(
                agent_id=agent_id,
                message_id=message.message_id,
                status="HANDLER_FAILED_UNACKNOWLEDGED",
                error_type=type(exc).__name__,
            )
        return DispatchResult(
            agent_id=agent_id,
            message_id=message.message_id,
            status="HANDLED",
            result=result,
        )
