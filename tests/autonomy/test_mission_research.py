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
