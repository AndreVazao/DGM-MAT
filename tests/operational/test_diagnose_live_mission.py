import pytest

from scripts.diagnose_live_mission import mission_checkpoint_status, validate_mission_goal


@pytest.mark.parametrize(
    "goal, expected_intent",
    [
        ("Lista os repositórios locais", "list_repositories"),
        ("pesquisa no código local o fluxo de aprovação", "local_research"),
        ("resumo da arquitetura do projeto", "architecture_summary"),
        ("check git status", "repository_status"),
        ("inventory of active engines", "engines_inventory"),
    ],
)
def test_diagnostic_accepts_only_read_only_auto_run_intents(goal, expected_intent):
    decision = validate_mission_goal(goal)

    assert decision.intent == expected_intent
    assert decision.supported is True
    assert decision.requires_approval is False


@pytest.mark.parametrize(
    "goal",
    [
        "create a script to list repositories",
        "research the web for a new provider",
        "sync DGM-MAT GitHub main into the isolated worktree",
        "orquestra uma nova estrutura organizacional",
    ],
)
def test_diagnostic_rejects_mutating_external_or_approval_required_goals(goal):
    with pytest.raises(ValueError, match="read-only auto-run allowlist"):
        validate_mission_goal(goal)


def test_checkpoint_status_survives_a_truncated_payload():
    report_mission = {
        "last_checkpoint_status": "COMPLETED",
        "last_checkpoint": {
            "truncated": True,
            "preview": "truncated payload",
        },
    }

    assert mission_checkpoint_status(report_mission) == "COMPLETED"


def test_checkpoint_status_falls_back_to_untruncated_checkpoint():
    assert mission_checkpoint_status({
        "last_checkpoint": {"status": "RUNNING"},
    }) == "RUNNING"
