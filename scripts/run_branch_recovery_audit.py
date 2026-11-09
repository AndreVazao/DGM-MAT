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

from core.repository_intelligence.branch_recovery_analyzer import BranchRecoveryAnalyzer


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# DGM-MAT — Branch Recovery Audit",
        "",
        f"Generated: {result.get('generated_at', 'unknown')}",
        f"Repository: `{result.get('repository')}`",
        f"Default branch: `{result.get('default_branch')}` @ `{result.get('default_sha')}`",
        "",
        "**Mode:** read-only. No refs or working-tree files were changed.",
        "",
        "## Working tree",
        "",
        f"- Dirty: **{result.get('working_tree_dirty')}**",
    ]
    dirty = result.get("working_tree_paths") or []
    if dirty:
        lines.extend(["- Paths:"] + [f"  - `{path}`" for path in dirty])
    lines.extend(["", "## Branch findings", "", "| Branch | State | Ahead | Behind | Recommendation |", "|---|---|---:|---:|---|"])
    for item in result.get("branches") or []:
        lines.append(
            f"| `{item['branch']}` | {item['status']} | {item['ahead_commits']} | "
            f"{item['behind_commits']} | {item['recommendation']} |"
        )
        if item.get("changed_files_vs_default"):
            lines.extend(["", f"### `{item['branch']}` — unique changed files", ""])
            for changed in item["changed_files_vs_default"]:
                lines.append(f"- **{changed['status']}** `{changed['path']}`")
            if item.get("unique_commit_subjects"):
                lines.extend(["", "Unique commits:"] + [f"- {subject}" for subject in item["unique_commit_subjects"]])
    lines.extend([
        "",
        "## Safety",
        "",
        "- This report is not merge or deletion authorization.",
        "- Dirty/untracked file contents were not read into the report.",
        "- Branches with unique work must be preserved until a reviewed destination is merged and verified.",
        "- Remote branches not present in the local object database remain unverified; use the GitHub portfolio compare evidence.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Git branch archaeology; no refs or files are modified.")
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--default-branch", required=True)
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "storage" / "runtime" / "branch_recovery")
    args = parser.parse_args()

    analyzer = BranchRecoveryAnalyzer()
    result = analyzer.audit_repository(args.repository, args.default_branch)
    result["generated_at"] = datetime.now(timezone.utc).isoformat()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_text = json.dumps(result, ensure_ascii=False, indent=2)
    md_text = render_markdown(result)
    json_path = args.output_dir / f"branch-audit-{stamp}.json"
    md_path = args.output_dir / f"branch-audit-{stamp}.md"
    json_path.write_text(json_text, encoding="utf-8")
    md_path.write_text(md_text, encoding="utf-8")
    (args.output_dir / "latest.json").write_text(json_text, encoding="utf-8")
    (args.output_dir / "latest.md").write_text(md_text, encoding="utf-8")
    print(json.dumps({
        "status": "completed",
        "json_report": str(json_path),
        "markdown_report": str(md_path),
        "branches": result["branch_count"],
        "dirty": result["working_tree_dirty"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
