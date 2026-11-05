from core.runtime.repository_root import resolve_repository_root


def test_source_runtime_resolves_nearest_git_checkout(tmp_path):
    repo = tmp_path / "repo"
    source = repo / "core" / "autonomy" / "mission_engine.py"
    source.parent.mkdir(parents=True)
    source.write_text("# test", encoding="utf-8")
    (repo / ".git").mkdir()

    assert resolve_repository_root(source, cwd=tmp_path / "elsewhere", frozen=False) == repo


def test_source_checkout_takes_precedence_over_unrelated_git_working_directory(tmp_path):
    repo = tmp_path / "project"
    unrelated = tmp_path / "unrelated"
    source = repo / "core" / "runtime" / "runtime.py"
    source.parent.mkdir(parents=True)
    source.write_text("# test", encoding="utf-8")
    (repo / ".git").mkdir()
    unrelated.mkdir()
    (unrelated / ".git").mkdir()

    assert resolve_repository_root(source, cwd=unrelated, frozen=False) == repo


def test_source_runtime_falls_back_to_current_git_checkout_when_source_is_external(tmp_path):
    repo = tmp_path / "working-copy"
    repo.mkdir()
    (repo / ".git").mkdir()

    assert resolve_repository_root(tmp_path / "external" / "module.py", cwd=repo, frozen=False) == repo


def test_frozen_runtime_resolves_installed_executable_project_root(tmp_path):
    repo = tmp_path / "DGM-MAT"
    installed = repo / "installed"
    installed.mkdir(parents=True)
    (repo / ".git").mkdir()
    executable = installed / "DGM-MAT.exe"
    executable.write_bytes(b"frozen")

    resolved = resolve_repository_root(
        tmp_path / "_MEIPASS" / "core" / "autonomy" / "mission_engine.py",
        cwd=installed, executable=executable, frozen=True,
    )

    assert resolved == repo


def test_frozen_runtime_prefers_explicit_repository_root(monkeypatch, tmp_path):
    repo = tmp_path / "operator-selected"
    repo.mkdir()
    monkeypatch.setenv("DGM_REPOSITORY_ROOT", str(repo))

    assert resolve_repository_root("missing.py", frozen=True) == repo
