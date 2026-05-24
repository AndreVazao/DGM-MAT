from enum import Enum

class AgentRole(Enum):
    REPO_OPERATOR = "repo_operator"
    EXECUTION_AGENT = "execution_agent"
    MEMORY_ARCHITECT = "memory_architect"
    RESEARCHER = "researcher"
