from core.autonomy.mission_intent_router import classify_mission_intent


def test_repository_listing_is_recognized_in_portuguese_and_english():
    for goal in ['lista as minhas repos', 'Mostra os meus repositórios', 'list repositories in workspace', 'show my repositories']:
        decision = classify_mission_intent(goal)
        assert decision.intent == 'list_repositories'
        assert decision.supported is True
        assert decision.requires_approval is False


def test_mutating_request_is_not_misclassified_as_read_only():
    for goal in ['create a script to list repositories', 'cria um script para listar repositórios', 'delete the old repository', 'corrigir o repositório']:
        decision = classify_mission_intent(goal)
        assert decision.intent == 'unsupported'
        assert decision.supported is False
        assert decision.requires_approval is True


def test_unknown_request_is_explicitly_unsupported():
    decision = classify_mission_intent('orquestra uma nova estrutura organizacional')
    assert decision.intent == 'unsupported'
    assert decision.supported is False
    assert 'No registered executor' in decision.reason


def test_invalid_goal_is_never_supported():
    decision = classify_mission_intent(' x ')
    assert decision.intent == 'invalid'
    assert decision.supported is False


def test_read_only_architecture_summary_is_recognized_in_portuguese_and_english():
    for goal in [
        "Prepare a summary of the repository architecture",
        "summarize the project structure",
        "resumo da arquitetura do projeto",
        "faz um resumo da estrutura do sistema",
        "analisa a arquitetura do meu projeto",
        "review the project architecture",
    ]:
        decision = classify_mission_intent(goal)
        assert decision.intent == "architecture_summary"
        assert decision.supported is True
        assert decision.requires_approval is False


def test_architecture_summary_never_overrides_a_mutating_request():
    for goal in [
        "summarize the architecture and update the README",
        "resume a arquitetura e corrige o código",
    ]:
        decision = classify_mission_intent(goal)
        assert decision.intent == "unsupported"
        assert decision.supported is False
        assert decision.requires_approval is True


def test_repository_status_is_recognized_in_portuguese_and_english():
    for goal in [
        "check git status",
        "show repository status",
        "mostra o estado do repositório",
        "status do repo",
    ]:
        decision = classify_mission_intent(goal)
        assert decision.intent == "repository_status"
        assert decision.supported is True
        assert decision.requires_approval is False


def test_repository_status_does_not_override_mutating_requests():
    decision = classify_mission_intent("update git status")
    assert decision.intent == "unsupported"
    assert decision.supported is False
    assert decision.requires_approval is True


def test_local_research_requires_local_scope_and_is_supported_in_portuguese_and_english():
    for goal in [
        "research the local repository for approval queue",
        "search the local codebase for mission recovery",
        "pesquisa no código local o fluxo de aprovação",
        "procura na documentação local por recuperação de missões",
    ]:
        decision = classify_mission_intent(goal)
        assert decision.intent == "local_research"
        assert decision.supported is True
        assert decision.requires_approval is False


def test_external_or_mutating_research_is_not_auto_routed_to_local_search():
    for goal in [
        "research the web for a new provider",
        "research the local repository and update the code",
    ]:
        decision = classify_mission_intent(goal)
        assert decision.intent == "unsupported"
        assert decision.supported is False
        assert decision.requires_approval is True

def test_github_main_sync_worktree_requires_operator_approval():
    decision = classify_mission_intent(
        "sync DGM-MAT GitHub main into the isolated worktree"
    )
    assert decision.intent == "repository_sync_worktree"
    assert decision.supported is True
    assert decision.requires_approval is True



def test_repository_audit_routes_to_bounded_local_research():
    for goal in [
        "audita o repositório DGM-MAT",
        "audit the local repository",
        "analisa o código local do DGM-MAT",
    ]:
        decision = classify_mission_intent(goal)
        assert decision.intent == "local_research"
        assert decision.supported is True
        assert decision.requires_approval is False


def test_dgm_mat_status_maps_to_read_only_system_summary():
    decision = classify_mission_intent("estado do DGM-MAT")
    assert decision.intent == "system_summary"
    assert decision.supported is True
    assert decision.requires_approval is False


def test_audit_cannot_hide_a_mutating_request():
    decision = classify_mission_intent("audita o repositório DGM-MAT e corrige o cockpit")
    assert decision.intent == "unsupported"
    assert decision.supported is False
    assert decision.requires_approval is True


def test_repository_research_and_status_report_routes_to_read_only_inventory():
    decision = classify_mission_intent(
        "faz uma pesquisa nas repos Barbuidos e reporta os seus estados"
    )

    assert decision.intent == "list_repositories"
    assert decision.supported is True
    assert decision.requires_approval is False


def test_repository_research_without_status_request_remains_local_research():
    decision = classify_mission_intent(
        "pesquisa nas repos por documentação de autenticação"
    )

    assert decision.intent == "local_research"
    assert decision.supported is True
    assert decision.requires_approval is False


def test_repository_documentation_search_is_not_misrouted_to_inventory():
    decision = classify_mission_intent(
        "search local repository documentation for allowed mission states"
    )

    assert decision.intent == "local_research"
    assert decision.supported is True
    assert decision.requires_approval is False


def test_external_repository_status_research_is_not_auto_routed_locally():
    decision = classify_mission_intent(
        "search the web for repositories and report their states"
    )

    assert decision.intent == "unsupported"
    assert decision.supported is False
    assert decision.requires_approval is True
