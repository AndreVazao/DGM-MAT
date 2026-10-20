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
