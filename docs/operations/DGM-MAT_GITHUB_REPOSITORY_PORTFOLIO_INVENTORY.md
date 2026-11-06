# DGM-MAT — GitHub Repository Portfolio Inventory

## Objective

The repository inventory must describe the real portfolio, not only local clones. It compares the authenticated GitHub account with local Git replicas and reports missing, duplicated, misconfigured, dirty, and out-of-sync repositories.

## Data sources

- Local Git repositories discovered in `C:\AI`, `C:\ProgramasGodMode`, `C:\DevopsGodMode`, and `C:\AndreOS-Memory`.
- Authenticated GitHub repository metadata through the installed `gh` CLI and GitHub GraphQL API.
- Local branch refs, working-tree status, HEAD SHA, and local default-branch SHA.
- GitHub default-branch SHA and remote branch names/SHAs.

## Required classifications

- `LOCAL_ONLY`: local Git repository has no matching owned GitHub repository.
- `GITHUB_ONLY`: owned GitHub repository has no matching local replica.
- `LOCAL_AND_GITHUB`: a local replica matches a GitHub repository by origin or, when origin is absent/malformed, by exact repository directory name.
- `GITHUB_UNVERIFIED`: GitHub could not be queried. The inventory must not falsely classify local repositories as local-only.
- `SYNCED`, `BEHIND`, `AHEAD`, `DIVERGED`: default-branch relationship when both commit objects are available locally.
- `COMMIT_MISMATCH_REMOTE_OBJECT_NOT_LOCAL`: remote SHA differs but the read-only scan does not possess the remote commit object; do not invent ahead/behind counts.
- `DEFAULT_BRANCH_MISSING` / `NOT_COMPARABLE`: local branch or remote default branch is absent.

## Branch comparison

Compare local branch names and commit SHAs with GitHub branch names and SHAs. Report local-only and GitHub-only branches, same-name branch SHA mismatches, and default-branch relationships. The inventory does not fetch or update refs. When a remote commit object is absent locally, it uses GitHub's read-only compare endpoint to obtain authoritative ahead/behind/diverged counts; if that API call also fails, the mismatch remains explicitly unverified rather than receiving invented counts.

## Safety rules

1. Read-only: never fetch, pull, push, commit, checkout, rebase, delete, create, or rewrite refs.
2. Never expose credentials embedded in Git remote URLs. Report only a boolean warning and a sanitized URL.
3. If GitHub authentication or the API fails, mark the remote side unavailable and local replicas unverified.
4. Match by canonical GitHub origin first. Use exact directory-name fallback only as a clearly labelled match method; never silently rewrite a remote.
5. Preserve duplicate local replicas as separate records and report how many distinct GitHub repositories they represent.
6. Keep `DGM-MAT-FULL-MIRROR` protected and audit-only.
7. Do not automatically repair remotes or synchronize repositories. Produce evidence and recommendations first.

## Mission integration

The existing read-only `list_repositories` mission now adds a `portfolio_inventory` object and comparison summary. The local scan is expanded to all configured roots and no longer stops at twenty repositories. The result retains the legacy `repositories` field for existing clients.

## Verified live scan — 6 November 2026

A read-only scan was executed on PC-Vazao-Anjos using the authenticated GitHub CLI account. GitHub GraphQL access succeeded.

| Metric | Result |
|---|---:|
| Local Git replicas discovered | 86 |
| Owned GitHub repositories | 81 |
| Local replicas matched to GitHub | 82 |
| Unique GitHub repositories matched | 80 |
| Duplicate local replicas | 2 |
| Local-only repositories | 4 |
| GitHub-only repositories | 1 |
| Dirty local working trees | 18 |
| Origin mismatches | 12 |
| Origins containing embedded credentials (value redacted) | 1 |
| Default branches synced | 54 |
| Default branches behind GitHub | 22 |
| Default branches ahead | 0 |
| Default branches diverged | 1 |
| Default branches missing locally | 2 |
| Default branches not comparable | 3 |
| Same-name branches compared | 85 |
| Same-name branches with equal SHA | 58 |
| Same-name branches requiring review | 27 |
| Local-only branches | 92 |
| GitHub-only branches | 174 |

The scanner used five local roots, including both C:/DevopsGodMode and C:/DevopGodMode. The result is a point-in-time snapshot. The 12 origin mismatches and one credential warning require inspection; no remote was rewritten. The credential warning belongs to the protected DGM-MAT-FULL-MIRROR clone; its value is never printed or persisted in the report. Do not use that mirror for synchronization.

The four local-only directories are DGM-Core-Backend, DGM-Docs, DGM-MAT-Cluster, and DGM-MAT-Studio. The GitHub-only repository is AndreVazao/Baribudos-Automation-Lab. The 22 behind and one diverged default branches are review candidates, not automatic merge/pull instructions.

Ten of the origin mismatches have malformed owner-only GitHub URLs ending in \`/AndreVazao/.git\`; gpt4free points to its upstream owner, and Lab-forge-icons has no readable origin in its worktree metadata. The exact repository names and sanitized URLs are in the JSON report. Do not auto-correct any remote until each intended origin is confirmed.

The full inventory is persisted by \`scripts/run_github_portfolio_inventory.py\` to \`storage/runtime/github_portfolio_inventory/latest.json\` and \`latest.md\`, with timestamped copies. The live scan used for this baseline completed with GitHub API access.

## Next stage

Create a review queue for origin corrections, branch synchronization proposals, and dirty working-tree triage. Each proposed action must include evidence and require explicit approval before changing refs or files. Conversation/AI history discovery remains a separate, higher-priority portfolio inventory.
