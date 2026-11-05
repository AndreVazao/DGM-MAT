from core.autonomy.mission_research import LocalMissionResearch


def test_local_research_returns_evidence_paths_without_network_or_commands(tmp_path):
    docs = tmp_path / 'docs'
    docs.mkdir()
    (docs / 'executor-guide.md').write_text(
        'The generic executor registry routes supported missions.\n', encoding='utf-8'
    )

    report = LocalMissionResearch(root=tmp_path).search(
        'generic executor registry', ['NotImplementedError']
    )

    assert report['status'] == 'EVIDENCE_FOUND'
    assert report['results'][0]['path'] == 'docs/executor-guide.md'
    assert report['results'][0]['line'] == 1
    assert report['external_calls'] == 0
    assert report['commands_executed'] == 0


def test_local_research_redacts_secrets_and_skips_secret_named_files(tmp_path):
    docs = tmp_path / 'docs'
    docs.mkdir()
    (docs / 'guide.md').write_text('Do not persist api_key=abcdef123456 in a result.\n', encoding='utf-8')
    (docs / 'api_key_notes.md').write_text('private api_key=ghp_abcdefghijklmnopqrstuvwxyz1234567890\n', encoding='utf-8')

    report = LocalMissionResearch(root=tmp_path).search('api_key result')
    rendered = str(report['results'])

    assert report['external_calls'] == 0
    assert 'abcdef123456' not in rendered
    assert 'ghp_abcdefghijklmnopqrstuvwxyz1234567890' not in rendered


def test_keywords_preserve_portuguese_accents_and_technical_identifiers():
    goal = (
        'Investigar no código local a implementação da SafeActionQueue, '
        'do MissionEngine e do executor, identificando os pontos de integração '
        'e os riscos para execução autónoma.'
    )

    keywords = LocalMissionResearch._keywords(goal)

    assert 'implementacao' in keywords
    assert 'safeactionqueue' in keywords
    assert 'missionengine' in keywords
    assert 'execucao' in keywords
    assert not {'da', 'do', 'e', 'para', 'aut'} & set(keywords)


def test_local_research_matches_accented_source_lines(tmp_path):
    docs = tmp_path / 'docs'
    docs.mkdir()
    source = docs / 'autonomia.md'
    source.write_text(
        'A execução autónoma depende da integração segura do executor.\n',
        encoding='utf-8',
    )

    report = LocalMissionResearch(root=tmp_path).search(
        'execucao autonoma integracao executor'
    )

    assert report['status'] == 'EVIDENCE_FOUND'
    assert report['results'][0]['path'] == 'docs/autonomia.md'
    assert report['results'][0]['matched_terms'] == [
        'integracao', 'autonoma', 'execucao', 'executor'
    ] or set(report['results'][0]['matched_terms']) == {
        'integracao', 'autonoma', 'execucao', 'executor'
    }


def test_technical_symbols_are_not_discarded_by_generic_query_terms(tmp_path):
    docs = tmp_path / 'docs'
    docs.mkdir()
    (docs / 'runtime.md').write_text(
        'MissionEngine dispatches approved SafeActionQueue actions to the executor.\n',
        encoding='utf-8',
    )

    goal = (
        'Investigar no código local a implementação da SafeActionQueue, '
        'do MissionEngine e do executor, identificando os pontos de integração '
        'e os riscos para execução autónoma.'
    )
    report = LocalMissionResearch(root=tmp_path).search(goal)

    assert report['status'] == 'EVIDENCE_FOUND'
    assert {'safeactionqueue', 'missionengine'} <= set(report['query_terms'])
    assert report['results'][0]['path'] == 'docs/runtime.md'
    assert {'safeactionqueue', 'missionengine'} <= set(report['results'][0]['matched_terms'])


def test_mission_research_prioritizes_domain_modules_within_file_budget(tmp_path):
    api = tmp_path / 'core' / 'api'
    autonomy = tmp_path / 'core' / 'autonomy'
    api.mkdir(parents=True)
    autonomy.mkdir(parents=True)
    for index in range(5):
        (api / f'api_{index}.py').write_text(
            'Generic API executor endpoint.\n', encoding='utf-8'
        )
    (autonomy / 'mission_engine.py').write_text(
        'MissionEngine registers SafeActionQueue for approved executor work.\n',
        encoding='utf-8',
    )

    report = LocalMissionResearch(root=tmp_path, max_files=2).search(
        'SafeActionQueue MissionEngine executor'
    )

    assert report['status'] == 'EVIDENCE_FOUND'
    assert report['files_scanned'] == 2
    assert any(
        item['path'] == 'core/autonomy/mission_engine.py'
        for item in report['results']
    )
    assert report['results'][0]['path'] == 'core/autonomy/mission_engine.py'


def test_local_research_limits_duplicate_lines_per_file(tmp_path):
    docs = tmp_path / 'docs'
    docs.mkdir()
    (docs / 'a.md').write_text(
        'executor registry\nexecutor workflow\nexecutor approval\n',
        encoding='utf-8',
    )
    (docs / 'b.md').write_text('executor validation\n', encoding='utf-8')

    report = LocalMissionResearch(root=tmp_path, max_results=4).search('executor')

    paths = [item['path'] for item in report['results']]
    assert paths.count('docs/a.md') <= 2
    assert 'docs/b.md' in paths
