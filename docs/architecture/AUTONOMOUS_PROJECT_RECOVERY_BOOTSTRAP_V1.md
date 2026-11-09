# Autonomous project recovery bootstrap — v1

**Status:** architecture contract only. The durable recovery supervisor and full end-to-end bootstrap are not yet implemented.

## Product contract

DGM-MAT should be able to run a durable, resumable recovery programme in the background while giving foreground user missions priority. Recovery must resume from the last committed checkpoint after interruption or restart.

**Activation is explicit.** The recovery bootstrap is a separate capability from repository inventory. It must not silently import conversations, scan arbitrary folders, launch coding agents, or consume external provider quotas on a fresh installation. Enable it only after the operator configures the source roots, authenticated providers, storage policy and resource budget. The existing repository-learning worker has its own profile policy: standard profile defaults ON; LOW_MEMORY (<4 GB RAM) defaults OFF; `DGM_REPOSITORY_LEARNING_ENABLED=1` explicitly opts in and `=0` disables it globally. These settings do not enable the broader recovery supervisor.

This architecture is not permission to merge unrelated products, delete branches, overwrite local work, publish content, or deploy. Recovery and analysis may be automated only within configured, read-only boundaries; cross-project integration and destructive operations remain approval-gated.

## Startup and recovery sequence

1. **Protect local evidence.** Inventory configured workspaces, repositories, branch/HEAD SHAs, dirty and untracked paths, worktrees and remotes (redacted). Never run reset, clean, checkout, stash, rebase, merge or push during discovery.
2. **Capture permitted context.** Import only conversation content and files exposed through authenticated, supported visible-browser or official export/connector mechanisms. A visible conversation list or navigation metadata is not proof that message content is available.
3. **Persist before interpretation.** Store imported records in the existing local Vault/archive with source IDs, timestamps, provider, content hashes, attachment references and resumable cursors. Preserve originals; deduplicate references without deleting source records.
4. **Build the project map.** Correlate explicit conversation links, project names, repository origins, GitHub full names, branch names and local paths. Record provenance and confidence. Ambiguous associations stay unresolved; never guess from title alone.
5. **Reconcile Git state.** Use local Git and authenticated host `gh` where configured. Compare local-only, remote-only and matched repositories/branches by SHA and commit graph. Record ahead/behind, unique commits, changed paths and dirty state. Secure local evidence first; prefer isolated mirrors/worktrees for remote fetch and comparison.
6. **Interpret current context.** Build a dated project brief from confirmed user decisions and current repository/runtime evidence. Recency alone is not authority; accepted decisions and verified tests outrank old brainstorming or assistant proposals.
7. **Classify findings.** Use current, already integrated, useful recovery candidate, superseded, conflicting, unverified or blocked. Every finding cites exact source conversation/message, repository, branch, commit and file path when available.
8. **Propose recovery.** Prepare a minimal plan in a new isolated branch/worktree pinned to an immutable base SHA. Verify imports, callers, dependencies, runtime registration, tests and security boundaries before proposing a change. Never edit the source branch.
9. **Validate and review.** Run bounded tests, compare baseline and candidate evidence, obtain an independent review and persist receipts/hashes. A successful review creates an operator approval request; it does not merge or deploy.
10. **Report safely.** Produce timestamped Markdown/JSON reports and a latest index. Sync only non-sensitive reports to AndreOS Memory after secret scanning and according to the operator's publication policy.

## Provider and agent boundaries

The conversation knowledge providers are exactly:
- ChatGPT
- Grok
- Gemini
- Claude
- DeepSeek
- Qwen

Use supported authenticated visible-browser sessions or official user exports/connectors. Claude historical recovery is capture-only; do not treat it as a consultation sender. Never scrape private browser databases, extract cookies/session tokens, bypass authentication, CAPTCHAs, Cloudflare or rate limits, or use residential proxies to evade controls. Missing message content and attachments remain explicitly unresolved; do not infer them from browser history metadata.

Local coding agents are separate from knowledge providers:
- Codex Free
- Claude Code Free

They currently run through FCC/NVIDIA NIM. This document does not enable unattended process execution. Any future executor must be separately implemented with explicit configuration, bounded sequential work, process/network isolation, read-only default permissions, durable receipts, cancellation and task-specific approval. No paid API or silent paid fallback is allowed.

## Background scheduling and pre-emption

One durable supervisor owns the recovery backlog and processes one bounded unit at a time:
- Foreground user mission: highest priority; pause background work at the next safe checkpoint.
- Safety, security or data-integrity incident: pause and alert.
- Explicitly enabled recovery bootstrap: resumable background priority.
- Periodic refresh: lowest priority.

A foreground mission must not erase the recovery checkpoint. On completion, the supervisor resumes only idempotent, checkpointed work. No concurrent writer may operate on the same repository/worktree. A restart reconstructs the queue from durable storage. On LOW_MEMORY hardware, default to no recovery autostart, one worker at most, small batches and conservative refresh intervals; never run multiple coding agents concurrently.

## Required durable records

- `recovery_runs`: run/install ID, status, stage, checkpoint, progress and last error.
- `source_accounts`: provider, non-secret account label, auth capability and last successful sync.
- `conversation_sources`: provider/source ID, timestamps, content hash, archive location and attachment references.
- `project_context`: project ID, brief version/hash and source-linked decisions.
- `repository_snapshots`: local path, GitHub identity, branch/HEAD snapshots, dirty state and observation time.
- `recovery_findings`: classification, evidence references, rationale, proposed destination and validation state.
- `background_work_queue`: priority, stage, checkpoint, idempotency key, attempts, retry time and last error.

Secrets and provider tokens remain in the existing local Vault/OS credential store. Never include them in reports, prompts, logs, Git remotes or SQLite recovery records.

## Existing implementation to reuse

- `RepositoryLearningService`: incremental local repository inventory, SQLite cursor, project trees and redaction. Standard/LOW_MEMORY autostart policy is implemented; it is not the recovery supervisor.
- `GitHubRepositoryPortfolio`: local/GitHub repository and branch inventory using host `gh`.
- `BranchRecoveryAnalyzer`: inspect its current implementation and CI status before relying on it.
- Existing conversation-recovery provider/browser components, Vault and durable task/message stores: reuse these; do not create a competing archive.
- `MissionEngine` and `SafeActionQueue`: foreground mission dispatch and durable work semantics.

## Acceptance gates

1. Recovery starts only after explicit operator configuration and reports its state in the cockpit.
2. Restart resumes at the last durable checkpoint without duplicate imports.
3. A foreground mission pauses recovery at a safe checkpoint and recovery resumes afterwards.
4. Provider outage does not lose progress from other providers.
5. Dirty local files and untracked files survive discovery unchanged.
6. GitHub-only work remains recoverable after local disk loss when remote access is configured.
7. Local/GitHub comparison identifies same-name SHA mismatches and unique commits.
8. Project context is versioned and source-linked before legacy code is judged.
9. Candidate recovery happens only in a new isolated branch/worktree pinned to a SHA.
10. Tests, independent reviewer receipt and explicit operator approval are required before merge.
11. LOW_MEMORY mode remains bounded and never starts multiple agents or recovery workers concurrently.
12. No provider scraping bypass, credential extraction, unapproved paid fallback or silent write operation occurs.

## Rollout sequence

A. Keep repository inventory and the broader recovery supervisor as separate capabilities, with independent status and controls.
B. Add durable recovery supervisor and foreground pre-emption, disabled until explicitly configured.
C. Integrate local Git + GitHub CLI snapshots and reports.
D. Integrate supported conversation ingestion and archive for the six configured knowledge providers.
E. Add source-grounded project context and branch recovery proposals in isolated worktrees.
F. Add controlled Codex/Claude Code process adapters only after isolation, receipts, bounded execution and explicit operator approval are proven.

Each stage requires separate tests and a separate review. Do not advertise 24/7 autonomous recovery until cold-start configuration, pre-emption, restart recovery, provider ingestion and low-memory E2E gates pass.
