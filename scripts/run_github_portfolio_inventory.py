from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.repository_intelligence.github_portfolio_inventory import GitHubRepositoryPortfolio


def _markdown_report(result: dict[str, Any]) -> str:
    summary = result.get("summary") or {}
    generated = result.get("generated_at", "unknown")
    lines = [
        "# DGM-MAT — GitHub Repository Portfolio Inventory",
        "",
        f"Generated: {generated}",
        "",
        f"- GitHub API available: **{result.get('github_api_available')}**",
        "- Scan mode: **read-only** (no fetch, pull, push, checkout, commit, or ref changes)",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "|---|---:|",
    ]
    for key, label in (
        ("local_repositories", "Local repositories"),
        ("github_repositories", "Owned GitHub repositories"),
        ("matched_repositories", "Matched local replicas"),
        ("unique_github_repositories_matched", "Unique matched GitHub repositories"),
        ("duplicate_local_replicas", "Duplicate local replicas"),
        ("local_only", "Local only"),
        ("github_only", "GitHub only"),
        ("dirty_local_repositories", "Dirty local working trees"),
        ("origin_mismatch", "Origin mismatches"),
        ("origin_credentials_present", "Origins containing credentials (values redacted)"),
        ("default_branch_synced", "Default branches synced"),
        ("default_branch_behind", "Default branches behind"),
        ("default_branch_ahead", "Default branches ahead"),
        ("default_branch_diverged", "Default branches diverged"),
        ("default_branch_mismatch_unverified", "Default branch mismatch unverified"),
        ("default_branch_missing", "Local default branch missing"),
        ("default_branch_not_comparable", "Default branches not comparable"),
        ("branches_compared_by_name", "Same-name branches compared"),
        ("branches_synced", "Same-name branches synced"),
        ("branches_commit_mismatch_review", "Same-name branches requiring review"),
        ("local_only_branches", "Local-only branches"),
        ("github_only_branches", "GitHub-only branches"),
    ):
        lines.append(f"| {label} | {summary.get(key, '—')} |")

    if result.get("github_error"):
        lines.extend(["", "## GitHub query error", "", str(result["github_error"])])

    lines.extend(["", "## Local-only repositories", ""])
    local_only = result.get("local_only") or []
    if not local_only:
        lines.append("None.")
    for item in local_only:
        lines.append(f"- **{item.get('name')}** — `{item.get('path')}`")

    lines.extend(["", "## GitHub-only repositories", ""])
    github_only = result.get("github_only") or []
    if not github_only:
        lines.append("None.")
    for item in github_only:
        lines.append(f"- **{item.get('full_name')}** — {item.get('url')}")

    lines.extend(["", "## Matched repositories and default-branch state", ""])
    for item in result.get("matched") or []:
        remote = item.get("remote_match") or {}
        comparison = item.get("default_branch_comparison") or {}
        lines.append(
            f"- **{remote.get('full_name', item.get('name'))}** — "
            f"`{comparison.get('status', 'UNKNOWN')}`; "
            f"match: `{item.get('match_method', 'unknown')}`; "
            f"dirty: `{item.get('dirty', False)}`; "
            f"local branches only: {len(item.get('local_only_branches') or [])}; "
            f"GitHub branches only: {len(item.get('github_only_branches') or [])}"
        )

    lines.extend([
        "",
        "## Interpretation and safeguards",
        "",
        "- This is a point-in-time inventory; it does not itself repair synchronization.",
        "- A BEHIND or DIVERGED status is evidence for review, not permission to merge or reset.",
        "- Origin mismatches and duplicate replicas require human review before any remote correction.",
        "- Branch inventories can be truncated when a GitHub repository has more than the API page size; the JSON records this condition.",
        "- No repository, branch, working tree, or remote reference was modified by this scan.",
        "",
        "The complete structured result is stored alongside this report as latest.json.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a read-only comparison of local Git replicas and owned GitHub repositories."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "storage" / "runtime" / "github_portfolio_inventory",
        help="Directory for timestamped JSON and Markdown reports.",
    )
    args = parser.parse_args()

    scanner = GitHubRepositoryPortfolio()
    result = scanner.build_inventory()
    result["generated_at"] = datetime.now(timezone.utc).isoformat()
    result["scan_roots"] = [str(path) for path in scanner.roots]
    args.output_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = args.output_dir / f"inventory-{stamp}.json"
    latest_json = args.output_dir / "latest.json"
    markdown_path = args.output_dir / f"inventory-{stamp}.md"
    latest_markdown = args.output_dir / "latest.md"

    serialized = json.dumps(result, ensure_ascii=False, indent=2)
    json_path.write_text(serialized, encoding="utf-8")
    latest_json.write_text(serialized, encoding="utf-8")
    markdown = _markdown_report(result)
    markdown_path.write_text(markdown, encoding="utf-8")
    latest_markdown.write_text(markdown, encoding="utf-8")

    print(json.dumps({
        "status": "completed" if result.get("github_api_available") else "github_unverified",
        "json_report": str(json_path),
        "markdown_report": str(markdown_path),
        "summary": result.get("summary"),
        "github_error": result.get("github_error"),
    }, ensure_ascii=False, indent=2))
    return 0 if result.get("github_api_available") else 2


if __name__ == "__main__":
    raise SystemExit(main())
