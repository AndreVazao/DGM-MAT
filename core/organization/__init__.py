"""DGM-MAT Digital Organization foundation."""

from .models import (
    AgentProfile,
    AgentStatus,
    Department,
    Evidence,
    EvolutionProposal,
    Message,
    MessagePriority,
    Task,
    TaskStatus,
)
from .registry import AgentRegistry
from .message_bus import InternalMessageBus
from .task_manager import OrganizationTaskManager
from .workspace import OrganizationWorkspace

__all__ = [
    "AgentProfile",
    "AgentRegistry",
    "AgentStatus",
    "Department",
    "Evidence",
    "EvolutionProposal",
    "InternalMessageBus",
    "Message",
    "MessagePriority",
    "OrganizationTaskManager",
    "OrganizationWorkspace",
    "Task",
    "TaskStatus",
]
