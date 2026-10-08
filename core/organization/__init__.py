"""DGM-MAT Digital Organization foundation."""

from .bootstrap import bootstrap_registry
from .capability_models import (
    CapabilityCandidate,
    CapabilityRequest,
    CapabilitySource,
    CapabilityStatus,
    RecruitmentOrder,
    RecruitmentStatus,
)
from .capability_registry import CapabilityRegistry
from .message_bus import InternalMessageBus
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
from .recruitment import RecruitmentDecision, RecruitmentEngine
from .registry import AgentRegistry
from .skill_forge import ForgeResult, SkillForge
from .source_discovery import LocalSourceDiscovery
from .task_manager import OrganizationTaskManager
from .workspace import OrganizationWorkspace

__all__ = [
    "AgentProfile", "AgentRegistry", "AgentStatus", "bootstrap_registry",
    "CapabilityCandidate", "CapabilityRegistry", "CapabilityRequest",
    "CapabilitySource", "CapabilityStatus", "Department", "Evidence",
    "EvolutionProposal", "ForgeResult", "InternalMessageBus",
    "LocalSourceDiscovery", "Message", "MessagePriority",
    "OrganizationTaskManager", "OrganizationWorkspace",
    "RecruitmentDecision", "RecruitmentEngine", "RecruitmentOrder",
    "RecruitmentStatus", "SkillForge", "Task", "TaskStatus",
]
