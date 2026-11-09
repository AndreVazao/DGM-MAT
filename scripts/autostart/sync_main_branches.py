from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

DGM_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HUB_ROOT = Path(r"C:\ProgramasGodMode\DGM-HUB")
REPORT_DIR = DGM_ROOT / "storage" / "runtime" / "main_sync"


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=90,
    )
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"git {args[0]} failed")
    return result


def checked_out_main(root: Path) -> Path | None:
    output = git(root, "worktree", "list", "--porcelain").stdout
    current: Path | None = None
    for line in output.splitlines() + [""]:
        if line.startswith("worktree "):
            current = Path(line[9:])
        elif line == "branch refs/heads/main" and current is not None:
            return current
        elif not line:
            current = None
    return None


def relation(local_is_ancestor: bool, remote_is_ancestor: bool) -> str:
    if local_is_ancestor and remote_is_ancestor:
        return "synced"
    if local_is_ancestor:
        return "behind"
    if remote_is_ancestor:
        return "ahead_requires_review"
    return "diverged_requires_review"


def sync_repository(name: str, root: Path, dry_run: bool = False) -> dict:
    if not root.exists() or git(root, "rev-parse", "--is-inside-work-tree", check=False).returncode:
        return {"repository": name, "path": str(root), "status": "missing_or_not_git"}

    fetch = git(root, "fetch", "origin", "main:refs/remotes/origin/main", check=False)
    if fetch.returncode:
        return {"repository": name, "path": str(root), "status": "fetch_failed", "error": fetch.stderr.strip()}

    local = git(root, "rev-parse", "refs/heads/main").stdout.strip()
    remote = git(root, "rev-parse", "refs/remotes/origin/main").stdout.strip()
    if local == remote:
        return {"repository": name, "path": str(root), "status": "synced", "local_main": local, "origin_main": remote}

    local_ancestor = git(root, "merge-base", "--is-ancestor", local, remote, check=False).returncode == 0
    remote_ancestor = git(root, "merge-base", "--is-ancestor", remote, local, check=False).returncode == 0
    state = relation(local_ancestor, remote_ancestor)
    result = {"repository": name, "path": str(root), "status": state, "local_main": local, "origin_main": remote}
    if state != "behind":
        return result

    worktree = checked_out_main(root)
    if worktree is not None:
        dirty = git(worktree, "status", "--porcelain").stdout.strip()
        if dirty:
            result["status"] = "behind_but_main_worktree_dirty"
            result["dirty_summary"] = dirty.splitlines()[:20]
            return result
        if dry_run:
            result["status"] = "would_fast_forward"
            return result
        update = git(worktree, "merge", "--ff-only", "origin/main", check=False)
        if update.returncode:
            result["status"] = "fast_forward_failed"
            result["error"] = update.stderr.strip()
            return result
        result["status"] = "fast_forwarded"
    else:
        if dry_run:
            result["status"] = "would_advance_main_ref"
            return result
        update = git(root, "update-ref", "refs/heads/main", remote, local, check=False)
        if update.returncode:
            result["status"] = "ref_update_failed"
            result["error"] = update.stderr.strip()
            return result
        result["status"] = "main_ref_advanced"
    result["local_main_after"] = git(root, "rev-parse", "refs/heads/main").stdout.strip()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe fast-forward-only synchronization of DGM-MAT and DGM-HUB main branches.")
    parser.add_argument("--hub-root", type=Path, default=DEFAULT_HUB_ROOT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    results = [
        sync_repository("DGM-MAT", DGM_ROOT, args.dry_run),
        sync_repository("DGM-HUB", args.hub_root, args.dry_run),
    ]
    report = {
        "schema": "dgm-main-only-sync.v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "policy": "fetch and fast-forward only; never push, force, rebase, reset, merge feature branches, or delete branches",
        "dry_run": args.dry_run,
        "repositories": results,
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "latest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# DGM-MAT / DGM-HUB — sincronização exclusiva de main", "", f"Data: {report['created_at']}", "", report["policy"], ""]
    lines.extend(f"- **{item['repository']}**: {item['status']} — {item.get('path', '')}" for item in results)
    (REPORT_DIR / "latest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if all(item["status"] in {"synced", "fast_forwarded", "main_ref_advanced", "would_fast_forward", "would_advance_main_ref"} for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
