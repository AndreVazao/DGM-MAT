# Branch recovery intelligence — read-only audit

## Objective

Give DGM-MAT an evidence-based way to inspect legacy local branches and identify work worth recovering without overwriting the current checkout or trusting commit counts alone.

## Existing portfolio inventory

The existing `GitHubRepositoryPortfolio` remains the source for discovering local repository clones, GitHub-owned repositories, origins, branch names/SHAs, dirty checkouts and local/GitHub mismatches. Its 2026-11-06 report is a historical snapshot, not current PC evidence.

## New local branch archaeology

`BranchRecoveryAnalyzer` inspects branch refs and Git objects already present in a local worktree:
- default branch SHA and current dirty/untracked paths;
- per-branch ahead/behind commit counts against the default branch;
- unique commit subjects and changed file paths;
- whether the branch tip is already an ancestor of the default branch;
- recommendations: already integrated, no unique commits, preserve unique work, reconcile file-by-file, or insufficient evidence.

Remote SHA comparison is performed only when the Git object is already present locally. If the object is absent, the analyzer reports `REMOTE_OBJECT_NOT_LOCAL` and leaves ahead/behind counts unknown. It never fetches merely to make the report look complete.

## Recovery classifications

| Finding | Recommendation |
|---|---|
| Branch tip is already in default history | Keep evidence; review dependencies/PRs before archive |
| No commits ahead, branch only behind | No unique committed work found; inspect dirty/untracked local files before archive |
| Ahead only | Preserve branch and review changed files/tests |
| Diverged | Preserve; reconcile file by file, never merge blindly |
| Remote object absent locally | Unknown; use GitHub compare API or an approved isolated mirror |
| Dirty worktree | Preserve; never checkout, reset, clean, stash or overwrite |

## Future integration protocol

1. Generate a read-only inventory report and timestamped evidence.
2. Compare same-name local/GitHub branch SHAs; use GitHub compare for remote refs whose objects are not local.
3. Inspect unique commits and changed files. For each candidate, compare current destination content, tests, callers, runtime registration and security policy.
4. Classify each candidate as already integrated, superseded, useful partial work, conflicting, or unverified.
5. If valuable work exists, create a dedicated recovery branch from the current approved base and port only the minimal necessary files/commits. Preserve the original branch.
6. Run focused tests and independent review; open a PR. Never delete the source branch until the destination is merged/verified and the operator approves cleanup.

## Safety

This increment is read-only. It does not fetch, pull, checkout, create branches, write patches, commit, merge, rebase, cherry-pick, push or delete. Dirty and untracked files are listed by path only; contents are not copied or modified. A future recovery-branch creator must be a separate approval-gated action with an immutable base SHA and source evidence.
