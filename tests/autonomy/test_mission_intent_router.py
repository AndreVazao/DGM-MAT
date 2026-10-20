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
    decision = classify_mission_intent('analisa a arquitetura do meu projeto')
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
