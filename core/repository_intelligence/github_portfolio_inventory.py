from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse


class GitHubRepositoryPortfolio:
    """Read-only comparison of local Git replicas with owned GitHub repositories.

    The scanner never fetches, pulls, pushes, checks out, commits, or changes refs.
    GitHub metadata is read through the authenticated GitHub CLI (gh).
    """

    DEFAULT_ROOTS = (
        Path("C:/AI"),
        Path("C:/ProgramasGodMode"),
        Path("C:/DevopsGodMode"),
        Path("C:/DevopGodMode"),
        Path("C:/AndreOS-Memory"),
    )

    def __init__(
        self,
        roots: tuple[Path, ...] | None = None,
        command_runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
        timeout: int = 20,
    ) -> None:
        self.roots = roots or self.DEFAULT_ROOTS
        self.command_runner = command_runner or subprocess.run
        self.timeout = timeout

    def build_inventory(self, local_repositories: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        local = local_repositories if local_repositories is not None else self.discover_local()
        local = [self._inspect_local(item) for item in local]
        remote, remote_error = self.fetch_github_repositories()

        if remote_error is not None:
            unverified = [{**item, "inventory_status": "GITHUB_UNVERIFIED"} for item in local]
            return {
                "schema": "dgm-mat.github-repository-portfolio.v1",
                "read_only": True,
                "github_api_available": False,
                "github_error": remote_error,
                "summary": {
                    "local_repositories": len(local),
                    "github_repositories": None,
                    "matched_repositories": 0,
                    "local_only": None,
                    "github_only": None,
                    "github_unverified": len(unverified),
                },
                "matched": [],
                "local_only": [],
                "github_only": [],
                "unverified_local": unverified,
                "github_repositories": [],
            }

        by_full_name = {item["full_name"].casefold(): item for item in remote}
        by_name = {item["name"].casefold(): item for item in remote}
        matched: list[dict[str, Any]] = []
        local_only: list[dict[str, Any]] = []
        claimed_remote: set[str] = set()

        for item in local:
            origin_full_name = self._github_full_name(item.get("origin"))
            remote_item = by_full_name.get((origin_full_name or "").casefold())
            match_method = "origin"
            if remote_item is None:
                remote_item = by_name.get(item["name"].casefold())
                match_method = "directory_name"
            if remote_item is None:
                item["inventory_status"] = "LOCAL_ONLY"
                item["remote_match"] = None
                local_only.append(item)
                continue

            full_name = remote_item["full_name"]
            claimed_remote.add(full_name.casefold())
            comparison = self._compare_default_branch(item, remote_item)
            item["inventory_status"] = "LOCAL_AND_GITHUB"
            item["match_method"] = match_method
            item["origin_matches_github"] = origin_full_name == full_name.casefold()
            item["remote_match"] = {
                "full_name": full_name,
                "url": remote_item["url"],
                "default_branch": remote_item.get("default_branch"),
                "default_branch_sha": remote_item.get("default_branch_sha"),
                "archived": remote_item.get("archived", False),
                "private": remote_item.get("private", False),
                "branch_count": len(remote_item.get("branches", [])),
                "branches_truncated": remote_item.get("branches_truncated", False),
            }
            item["default_branch_comparison"] = comparison
            local_names = set(item.get("local_branches", []))
            remote_names = {branch["name"] for branch in remote_item.get("branches", [])}
            item["local_only_branches"] = sorted(local_names - remote_names)
            item["github_only_branches"] = sorted(remote_names - local_names)
            item["branch_name_intersection"] = sorted(local_names & remote_names)
            local_shas = item.get("local_branch_shas", {})
            remote_shas = {
                branch["name"]: branch.get("sha")
                for branch in remote_item.get("branches", [])
            }
            item["branch_comparisons"] = [
                {
                    "name": name,
                    "local_sha": local_shas.get(name),
                    "github_sha": remote_shas.get(name),
                    "status": (
                        "SYNCED"
                        if local_shas.get(name) and local_shas.get(name) == remote_shas.get(name)
                        else "COMMIT_MISMATCH_REVIEW"
                    ),
                }
                for name in sorted(local_names & remote_names)
            ]
            matched.append(item)

        github_only = [
            item for item in remote if item["full_name"].casefold() not in claimed_remote
        ]
        branch_statuses = [
            item.get("default_branch_comparison", {}).get("status")
            for item in matched
        ]
        branch_comparisons = [
            comparison
            for repo in matched
            for comparison in repo.get("branch_comparisons", [])
        ]
        summary = {
            "local_repositories": len(local),
            "github_repositories": len(remote),
            "matched_repositories": len(matched),
            "matched_local_replicas": len(matched),
            "unique_github_repositories_matched": len(claimed_remote),
            "duplicate_local_replicas": len(matched) - len(claimed_remote),
            "local_only": len(local_only),
            "github_only": len(github_only),
            "dirty_local_repositories": sum(item.get("dirty", False) for item in local),
            "origin_mismatch": sum(
                item.get("inventory_status") == "LOCAL_AND_GITHUB"
                and not item.get("origin_matches_github", False)
                for item in local
            ),
            "origin_credentials_present": sum(item.get("origin_credentials_present", False) for item in local),
            "default_branch_synced": branch_statuses.count("SYNCED"),
            "default_branch_behind": branch_statuses.count("BEHIND"),
            "default_branch_ahead": branch_statuses.count("AHEAD"),
            "default_branch_diverged": branch_statuses.count("DIVERGED"),
            "default_branch_mismatch_unverified": branch_statuses.count("COMMIT_MISMATCH_REMOTE_OBJECT_NOT_LOCAL"),
            "default_branch_missing": branch_statuses.count("DEFAULT_BRANCH_MISSING"),
            "default_branch_not_comparable": branch_statuses.count("NOT_COMPARABLE"),
            "branches_compared_by_name": len(branch_comparisons),
            "branches_synced": sum(item["status"] == "SYNCED" for item in branch_comparisons),
            "branches_commit_mismatch_review": sum(
                item["status"] != "SYNCED" for item in branch_comparisons
            ),
            "local_only_branches": sum(len(item.get("local_only_branches", [])) for item in matched),
            "github_only_branches": sum(len(item.get("github_only_branches", [])) for item in matched),
        }
        return {
            "schema": "dgm-mat.github-repository-portfolio.v1",
            "read_only": True,
            "github_api_available": remote_error is None,
            "github_error": remote_error,
            "summary": summary,
            "matched": matched,
            "local_only": local_only,
            "github_only": github_only,
            "github_repositories": remote,
        }

    def discover_local(self) -> list[dict[str, Any]]:
        found: dict[str, Path] = {}
        for root in self.roots:
            if not root.exists():
                continue
            candidates = [root] if (root / ".git").exists() else []
            try:
                candidates.extend(item for item in root.iterdir() if item.is_dir())
            except (OSError, PermissionError):
                continue
            for path in candidates:
                if (path / ".git").exists():
                    found[str(path.resolve()).casefold()] = path
        return [
            {"name": path.name, "path": str(path)}
            for path in sorted(found.values(), key=lambda value: value.name.casefold())
        ]

    def fetch_github_repositories(self) -> tuple[list[dict[str, Any]], str | None]:
        query = """
        query {
          viewer {
            repositories(first: 100, after: __CURSOR__, ownerAffiliations: OWNER) {
              nodes {
                nameWithOwner
                name
                isPrivate
                isArchived
                url
                defaultBranchRef {
                  name
                  target { ... on Commit { oid } }
                }
                refs(refPrefix: "refs/heads/", first: 100) {
                  nodes { name target { ... on Commit { oid } } }
                  pageInfo { hasNextPage }
                }
              }
              pageInfo { hasNextPage endCursor }
            }
          }
        }
        """
        repositories: list[dict[str, Any]] = []
        cursor: str | None = None
        try:
            while True:
                page_query = query.replace("__CURSOR__", "null" if cursor is None else json.dumps(cursor))
                result = self.command_runner(
                    ["gh", "api", "graphql", "-f", f"query={page_query}"],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    check=False,
                )
                if result.returncode != 0:
                    return [], (result.stderr or result.stdout or "gh api graphql failed").strip()
                payload = json.loads(result.stdout)
                if payload.get("errors"):
                    return [], json.dumps(payload["errors"], ensure_ascii=False)
                connection = payload["data"]["viewer"]["repositories"]
                for node in connection.get("nodes", []):
                    default_ref = node.get("defaultBranchRef") or {}
                    branch_connection = node.get("refs") or {}
                    branch_page = branch_connection.get("pageInfo") or {}
                    repositories.append({
                        "full_name": node["nameWithOwner"],
                        "name": node["name"],
                        "url": node["url"],
                        "private": bool(node.get("isPrivate")),
                        "archived": bool(node.get("isArchived")),
                        "default_branch": default_ref.get("name"),
                        "default_branch_sha": (default_ref.get("target") or {}).get("oid"),
                        "branches": [
                            {"name": branch["name"], "sha": (branch.get("target") or {}).get("oid")}
                            for branch in branch_connection.get("nodes", [])
                        ],
                        "branches_truncated": bool(branch_page.get("hasNextPage")),
                    })
                page = connection.get("pageInfo") or {}
                if not page.get("hasNextPage"):
                    break
                cursor = page.get("endCursor")
                if not cursor:
                    return repositories, "GitHub pagination returned hasNextPage without endCursor"
            return repositories, None
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError, KeyError, TypeError) as exc:
            return [], f"{type(exc).__name__}: {exc}"

    def _inspect_local(self, item: dict[str, Any]) -> dict[str, Any]:
        path = Path(item["path"])
        raw_origin = self._git(path, "remote", "get-url", "origin")
        origin_credentials_present = self._origin_has_credentials(raw_origin)
        origin = self._sanitize_origin(raw_origin)
        branch = self._git(path, "branch", "--show-current")
        head = self._git(path, "rev-parse", "HEAD")
        status = self._git(path, "status", "--porcelain")
        branches = self._git(
            path, "for-each-ref", "--format=%(refname:short)|%(objectname)", "refs/heads"
        )
        branch_refs = {}
        for line in branches.splitlines():
            name, separator, sha = line.partition("|")
            if separator and name.strip() and sha.strip():
                branch_refs[name.strip()] = sha.strip()
        return {
            **item,
            "origin": origin or None,
            "origin_credentials_present": origin_credentials_present,
            "branch": branch or None,
            "head_sha": head or None,
            "dirty": bool(status),
            "working_tree_changes": len([line for line in status.splitlines() if line.strip()]),
            "local_branches": sorted(branch_refs),
            "local_branch_shas": branch_refs,
        }

    def _compare_default_branch(self, local: dict[str, Any], remote: dict[str, Any]) -> dict[str, Any]:
        branch = remote.get("default_branch")
        remote_sha = remote.get("default_branch_sha")
        if not branch or not remote_sha:
            return {"status": "NOT_COMPARABLE", "reason": "GitHub repository has no default branch commit"}
        local_sha = self._git(Path(local["path"]), "rev-parse", f"refs/heads/{branch}")
        if not local_sha:
            return {"status": "DEFAULT_BRANCH_MISSING", "branch": branch, "remote_sha": remote_sha}
        if local_sha == remote_sha:
            return {"status": "SYNCED", "branch": branch, "local_sha": local_sha, "remote_sha": remote_sha}
        path = Path(local["path"])
        remote_object_exists = self._git(
            path, "cat-file", "-e", f"{remote_sha}^{{commit}}",
            allow_failure=True, return_code=True,
        ) == "0"
        if not remote_object_exists:
            github_comparison = self._github_compare(remote["full_name"], local_sha, remote_sha)
            if github_comparison is not None:
                return {
                    **github_comparison,
                    "branch": branch,
                    "local_sha": local_sha,
                    "remote_sha": remote_sha,
                    "comparison_source": "github_compare_api",
                }
            return {
                "status": "COMMIT_MISMATCH_REMOTE_OBJECT_NOT_LOCAL",
                "branch": branch,
                "local_sha": local_sha,
                "remote_sha": remote_sha,
                "reason": "Remote commit object is absent locally and GitHub compare API was unavailable; ahead/behind counts remain unknown.",
            }
        local_is_ancestor = self._git(path, "merge-base", "--is-ancestor", local_sha, remote_sha, allow_failure=True, return_code=True)
        remote_is_ancestor = self._git(path, "merge-base", "--is-ancestor", remote_sha, local_sha, allow_failure=True, return_code=True)
        if local_is_ancestor == "0":
            status = "BEHIND"
        elif remote_is_ancestor == "0":
            status = "AHEAD"
        else:
            status = "DIVERGED"
        counts = self._git(path, "rev-list", "--left-right", "--count", f"{local_sha}...{remote_sha}")
        ahead = behind = None
        try:
            ahead, behind = [int(value) for value in counts.split()]
        except (ValueError, TypeError):
            pass
        return {
            "status": status,
            "branch": branch,
            "local_sha": local_sha,
            "remote_sha": remote_sha,
            "ahead": ahead,
            "behind": behind,
        }

    def _github_compare(
        self, full_name: str, local_sha: str, remote_sha: str
    ) -> dict[str, Any] | None:
        endpoint = f"repos/{full_name}/compare/{local_sha}...{remote_sha}"
        try:
            result = self.command_runner(
                [
                    "gh", "api", endpoint, "--jq",
                    "{status: .status, ahead_by: .ahead_by, behind_by: .behind_by}",
                ],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )
            if result.returncode != 0:
                return None
            payload = json.loads(result.stdout)
            status_map = {
                "identical": "SYNCED",
                "ahead": "BEHIND",
                "behind": "AHEAD",
                "diverged": "DIVERGED",
            }
            status = status_map.get(str(payload.get("status", "")).casefold())
            if status is None:
                return None
            return {
                "status": status,
                "ahead": payload.get("behind_by", 0),
                "behind": payload.get("ahead_by", 0),
            }
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError, TypeError):
            return None

    def _git(self, path: Path, *args: str, allow_failure: bool = False, return_code: bool = False) -> str:
        try:
            result = self.command_runner(
                ["git", "-c", f"safe.directory={path}", *args],
                cwd=str(path),
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
            )
            if return_code:
                return str(result.returncode)
            if result.returncode != 0 and not allow_failure:
                return ""
            return result.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return ""

    @staticmethod
    def _origin_has_credentials(origin: str | None) -> bool:
        if not origin:
            return False
        try:
            parsed = urlparse(origin.strip())
            return parsed.username is not None or parsed.password is not None
        except ValueError:
            return False

    @staticmethod
    def _sanitize_origin(origin: str | None) -> str | None:
        if not origin:
            return None
        try:
            parsed = urlparse(origin.strip())
            if parsed.username is None and parsed.password is None:
                return origin.strip()
            host = parsed.hostname or ""
            if parsed.port:
                host = f"{host}:{parsed.port}"
            return parsed._replace(netloc=host).geturl()
        except ValueError:
            return "[invalid-origin-redacted]"

    @staticmethod
    def _github_full_name(origin: str | None) -> str | None:
        if not origin:
            return None
        value = origin.strip()
        if value.startswith("git@github.com:"):
            path = value.split(":", 1)[1]
        else:
            parsed = urlparse(value)
            if parsed.netloc.casefold() not in {"github.com", "www.github.com"}:
                return None
            path = parsed.path.strip("/")
        if path.endswith(".git"):
            path = path[:-4]
        parts = path.split("/")
        if len(parts) != 2 or not all(parts):
            return None
        return f"{parts[0]}/{parts[1]}".casefold()
