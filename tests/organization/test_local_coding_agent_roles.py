from core.organization.models import AgentStatus
from core.organization.office import bootstrap_full_office


def test_codex_and_claude_code_roles_remain_offline_and_read_only_until_host_validation():
    registry = bootstrap_full_office()

    for agent_id in ("agent:codex-cli", "agent:claude-code-cli"):
        profile = registry.get_agent(agent_id)
        assert profile is not None
        assert profile.status is AgentStatus.OFFLINE
        assert "repo:read" in profile.permissions
        assert "reports:write" in profile.permissions
        assert not any(permission.startswith("repo:write") for permission in profile.permissions)
        assert profile.metadata["execution_maturity"] == "ROLE_DEFINED_ONLY"
        assert "not yet host-validated" in profile.metadata["activation_blocker"]
