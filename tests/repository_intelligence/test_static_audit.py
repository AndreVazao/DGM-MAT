from __future__ import annotations

import json
from pathlib import Path

from core.repository_intelligence.static_audit import audit_project
from core.vault.catalog import VaultCatalog


def _fixture(tmp_path: Path):
    repo = tmp_path / "source" / "sample-project"
    (repo / "src" / "pkg").mkdir(parents=True)
    (repo / "web").mkdir()
    (repo / "src" / "pkg" / "__init__.py").write_text("from .module import public_api\n", encoding="utf-8")
    (repo / "src" / "pkg" / "module.py").write_text(
        "__all__ = ['public_api']\ndef public_api():\n    return 1\n", encoding="utf-8"
    )
    (repo / "src" / "broken.py").write_text("def broken(:\n", encoding="utf-8")
    (repo / "web" / "main.ts").write_text(
        "import { helper } from './helper';\nexport const main = () => helper();\n", encoding="utf-8"
    )
    (repo / "web" / "helper.ts").write_text("export const helper = () => 1;\n", encoding="utf-8")
    (repo / "web" / "missing.ts").write_text("import x from './not-here';\n", encoding="utf-8")
    (repo / "pyproject.toml").write_text(
        "[project]\nname = 'sample-project'\ndependencies = ['requests>=2', 'httpx']\n", encoding="utf-8"
    )
    (repo / "package.json").write_text('{"dependencies":{"react":"^18"},"devDependencies":{"vite":"^5"}}', encoding="utf-8")
    (repo / ".env").write_text("API_KEY=must-not-be-read\n", encoding="utf-8")
    vault = VaultCatalog(vault_root=tmp_path / "private-vault")
    vault.register_project("sample-project", "Sample Project", repo)
    snapshot = vault.snapshot_repository("sample-project", repo)
    return repo, vault, snapshot


def test_static_audit_extracts_python_js_and_manifest_evidence(tmp_path: Path):
    repo, vault, snapshot = _fixture(tmp_path)
    report = audit_project(vault=vault, project_id="sample-project")
    assert report["snapshot_id"] == snapshot["snapshot_id"]
    assert report["summary"]["python_files"] == 3
    assert report["summary"]["javascript_files"] == 3
    assert report["summary"]["syntax_errors"] == 1
    assert report["summary"]["unresolved_relative_imports"] == 1
    assert report["manifests"]["python"] == ["httpx", "requests"]
    assert report["manifests"]["javascript"] == ["react", "vite"]
    module = next(item for item in report["python"] if item["path"] == "src/pkg/module.py")
    assert module["exports"] == ["public_api"]
    assert Path(report["report_path"]).is_relative_to(vault.root)
    assert Path(report["markdown_path"]).is_file()
    assert ".env" not in json.dumps(report)


def test_static_audit_is_read_only_and_reuses_unchanged_fingerprint(tmp_path: Path):
    repo, vault, _ = _fixture(tmp_path)
    before = {p.relative_to(repo).as_posix(): p.read_bytes() for p in repo.rglob("*") if p.is_file()}
    first = audit_project(vault=vault, project_id="sample-project")
    second = audit_project(vault=vault, project_id="sample-project")
    after = {p.relative_to(repo).as_posix(): p.read_bytes() for p in repo.rglob("*") if p.is_file()}
    assert before == after
    assert first["audit_fingerprint"] == second["audit_fingerprint"]
    assert first["reused"] is False
    assert second["reused"] is True


def test_static_audit_requires_existing_vault_snapshot(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    vault = VaultCatalog(vault_root=tmp_path / "private-vault")
    vault.register_project("empty", "Empty", repo)
    try:
        audit_project(vault=vault, project_id="empty")
    except ValueError as exc:
        assert "snapshot" in str(exc).casefold()
    else:
        raise AssertionError("audit must not scan a repository outside an immutable Vault snapshot")


def test_static_audit_rejects_unbounded_limits(tmp_path: Path):
    _, vault, _ = _fixture(tmp_path)
    try:
        audit_project(vault=vault, project_id="sample-project", max_files=999999)
    except ValueError as exc:
        assert "limit" in str(exc).casefold()
    else:
        raise AssertionError("unbounded file limits must be rejected")


def test_static_audit_api_returns_evidence_paths_and_read_only_guarantees(tmp_path: Path, monkeypatch):
    from core.api import repository_learning_api
    repo, vault, snapshot = _fixture(tmp_path)
    monkeypatch.setattr(VaultCatalog, "default_root", staticmethod(lambda: vault.root))
    result = repository_learning_api.static_project_audit(project_id="sample-project")
    assert result["status"] == "complete"
    assert result["snapshot_id"] == snapshot["snapshot_id"]
    assert result["read_only"] is True
    assert result["code_executed"] is False
    assert Path(result["report_path"]).is_file()


def test_static_audit_refuses_files_changed_after_snapshot(tmp_path: Path):
    repo, vault, _ = _fixture(tmp_path)
    target = repo / "src" / "pkg" / "module.py"
    target.write_text("def changed_after_snapshot():\n    return 'new code'\n", encoding="utf-8")
    report = audit_project(vault=vault, project_id="sample-project")
    assert not any(item["path"] == "src/pkg/module.py" for item in report["python"])
    changed = [item for item in report["findings"] if item["kind"] == "snapshot_file_changed"]
    assert any(item["path"] == "src/pkg/module.py" for item in changed)
