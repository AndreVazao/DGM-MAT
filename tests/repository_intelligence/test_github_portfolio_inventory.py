import json
import subprocess
from pathlib import Path

from core.repository_intelligence.github_portfolio_inventory import GitHubRepositoryPortfolio


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _repo(tmp_path: Path, name: str = "demo") -> Path:
    repo = tmp_path / name
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "initial")
    return repo


def test_inventory_matches_local_repo_by_name_when_origin_is_wrong(tmp_path):
    repo = _repo(tmp_path)
    _git(repo, "remote", "add", "origin", "https://github.com/AndreVazao/.git")
    sha = _git(repo, "rev-parse", "HEAD")

    class Runner:
        def __call__(self, command, **kwargs):
            if command[0] == "gh":
                payload = {
                    "data": {"viewer": {"repositories": {
                        "nodes": [{
                            "nameWithOwner": "AndreVazao/demo",
                            "name": "demo",
                            "url": "https://github.com/AndreVazao/demo",
                            "isPrivate": False,
                            "isArchived": False,
                            "defaultBranchRef": {"name": "main", "target": {"oid": sha}},
                            "refs": {"nodes": [{"name": "main", "target": {"oid": sha}}], "pageInfo": {"hasNextPage": False}},
                        }],
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                    }}}
                }
                return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")
            return subprocess.run(command, **kwargs)

    result = GitHubRepositoryPortfolio(
        roots=(tmp_path,),
        command_runner=Runner(),
    ).build_inventory([{"name": "demo", "path": str(repo)}])

    assert result["summary"]["matched_repositories"] == 1
    assert result["summary"]["local_only"] == 0
    assert result["summary"]["github_only"] == 0
    assert result["matched"][0]["match_method"] == "directory_name"
    assert result["matched"][0]["origin_matches_github"] is False
    assert result["matched"][0]["default_branch_comparison"]["status"] == "SYNCED"
    assert result["matched"][0]["branch_comparisons"][0]["status"] == "SYNCED"


def test_inventory_separates_local_only_and_github_only(tmp_path):
    repo = _repo(tmp_path, "local-project")

    class Runner:
        def __call__(self, command, **kwargs):
            payload = {
                "data": {"viewer": {"repositories": {
                    "nodes": [{
                        "nameWithOwner": "AndreVazao/remote-project",
                        "name": "remote-project",
                        "url": "https://github.com/AndreVazao/remote-project",
                        "isPrivate": True,
                        "isArchived": False,
                        "defaultBranchRef": None,
                        "refs": {"nodes": [], "pageInfo": {"hasNextPage": False}},
                    }],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }}}
            }
            return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")

    result = GitHubRepositoryPortfolio(
        roots=(tmp_path,),
        command_runner=Runner(),
    ).build_inventory([{"name": repo.name, "path": str(repo)}])

    assert result["summary"]["local_only"] == 1
    assert result["summary"]["github_only"] == 1
    assert result["local_only"][0]["inventory_status"] == "LOCAL_ONLY"
    assert result["github_only"][0]["full_name"] == "AndreVazao/remote-project"


def test_github_origin_parser_supports_https_and_ssh():
    parse = GitHubRepositoryPortfolio._github_full_name
    assert parse("https://github.com/AndreVazao/DGM-MAT.git") == "andrevazao/dgm-mat"
    assert parse("git@github.com:AndreVazao/DGM-MAT.git") == "andrevazao/dgm-mat"
    assert parse("https://example.com/org/repo.git") is None


def test_origin_with_embedded_credentials_is_redacted():
    raw = "https://user:secret-token@github.com/AndreVazao/demo.git"
    assert GitHubRepositoryPortfolio._origin_has_credentials(raw) is True
    safe = GitHubRepositoryPortfolio._sanitize_origin(raw)
    assert safe == "https://github.com/AndreVazao/demo.git"
    assert "secret-token" not in safe


def test_github_failure_never_claims_local_only(tmp_path):
    repo = _repo(tmp_path, "offline-project")

    class Runner:
        def __call__(self, command, **kwargs):
            return subprocess.CompletedProcess(command, 1, "", "authentication unavailable")

    result = GitHubRepositoryPortfolio(
        roots=(tmp_path,),
        command_runner=Runner(),
    ).build_inventory([{"name": repo.name, "path": str(repo)}])

    assert result["github_api_available"] is False
    assert result["summary"]["github_unverified"] == 1
    assert result["summary"]["local_only"] is None
    assert result["unverified_local"][0]["inventory_status"] == "GITHUB_UNVERIFIED"



def test_default_branch_uses_github_compare_when_remote_object_is_not_local(tmp_path):
    repo = _repo(tmp_path, "compare-project")
    local_sha = _git(repo, "rev-parse", "HEAD")
    remote_sha = "f" * 40

    class Runner:
        def __call__(self, command, **kwargs):
            if command[0] == "gh":
                assert command[2].startswith("repos/AndreVazao/compare-project/compare/")
                payload = {"status": "ahead", "ahead_by": 3, "behind_by": 0}
                return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")
            return subprocess.run(command, **kwargs)

    inventory = GitHubRepositoryPortfolio(command_runner=Runner())
    comparison = inventory._compare_default_branch(
        {"path": str(repo)},
        {
            "full_name": "AndreVazao/compare-project",
            "default_branch": "main",
            "default_branch_sha": remote_sha,
        },
    )

    assert comparison["status"] == "BEHIND"
    assert comparison["ahead"] == 0
    assert comparison["behind"] == 3
    assert comparison["comparison_source"] == "github_compare_api"
    assert comparison["local_sha"] == local_sha
