# Autonomous project recovery bootstrap — v1

**Status:** architecture and implementation plan; not yet enabled in production runtime.

## Product contract

A fresh DGM-MAT installation must start a durable, resumable recovery programme without requiring the operator to create a mission. User-created missions pre-empt background recovery. When the foreground queue becomes idle, the supervisor resumes the exact interrupted recovery checkpoint.

This is not permission to merge unrelated products, delete branches, overwrite local work, publish content, or deploy. Recovery and analysis are autonomous; cross-project integration and destructive operations remain approval-gated.

## Startup sequence

1. **Protect local evidence.** Detect the current workspace, Git repositories, current branch, HEAD SHA, dirty paths, untracked paths, worktrees, remotes (redacted), and local conversation/export stores. Never run reset, clean, checkout, stash, rebase, merge, or push during discovery.
2. **Capture available context.** Import only conversations and files exposed through authenticated, supported provider/browser export mechanisms. Preserve original source identifiers, provider, timestamps, attachments metadata, project attribution confidence, and content hashes. Never scrape private browser databases or bypass provider authentication.
3. **Persist before interpretation.** Store raw imported records in a local append-only archive, with a manifest and SHA-256. Maintain resumable cursors. Deduplicate by source ID and content hash without deleting source records.
4. **Build project map.** Correlate conversation evidence, project names, repository origins, local paths, GitHub full names, branch names, and explicit links. Every association has provenance and confidence; ambiguous links remain unresolved.
5. **Reconcile Git state.** Use local Git and the authenticated `gh` CLI directly from the host. Inventory local-only, GitHub-only and matched repositories; compare default branches and every same-name branch by SHA and commit graph. Record ahead/behind, unique commits, changed paths, dirty worktrees and missing remote objects. Fetching remote refs is allowed only after the local evidence snapshot is secured; never fetch into a dirty user checkout when it could interfere with work. Prefer a separate mirror/worktree.
6. **Interpret against current context.** Build a dated project brief from the newest confirmed decisions and current documentation before judging old code. Conversation recency alone is not authority; explicit accepted decisions and current tests/runtime evidence outrank old brainstorming.
7. **Classify.** Each finding is one of: current, already integrated, useful recovery candidate, superseded, conflicting, unverified, or blocked. Explain why and cite exact source conversation, repository, branch, commit and file paths.
8. **Propose recovery.** For useful candidates, prepare a plan and an isolated recovery branch/worktree pinned to an immutable base SHA. Port minimal changes only after checking imports, callers, dependencies, runtime registration, tests, security boundaries and current project brief. Never modify the source branch.
9. **Validate and review.** Run bounded tests, compare baseline vs candidate, obtain an independent reviewer, persist receipts and hashes. A successful review creates an operator approval request; it does not silently merge or deploy.
10. **Publish reports.** Maintain timestamped JSON/Markdown reports plus a latest index in DGM-MAT storage, and optionally sync non-sensitive reports to the dedicated memory/report repository only after secret scanning and operator-configured publication policy.

## Conversation recovery — provider boundaries

- **ChatGPT, Grok, Gemini, DeepSeek and Qwen:** use supported authenticated browser sessions or official user exports/connectors. An installed browser or visible conversation list does not prove message content is accessible. Never infer content from history metadata.
- **Zia:** treat as a first-class source only after identifying its actual provider, account/session, export/API capability and consent boundary. Do not guess an endpoint or claim recovery from navigation metadata.
- Store attachments only when bytes are actually available and permitted. Record missing attachments as unresolved references.
- If a provider is unavailable, preserve the checkpoint and continue with other sources; do not block repository recovery.

## Background scheduler and pre-emption

One durable supervisor owns the recovery backlog. It runs a bounded unit of work per tick, then yields:
- Foreground user mission: highest priority; pause background work at the next safe checkpoint.
- Safety/security or data-integrity incident: immediate pause and alert.
- Recovery bootstrap: resumable background priority.
- Periodic refresh: lowest priority.

A user mission must not erase the recovery checkpoint. On completion, the supervisor re-queues the interrupted stage. No concurrent writer may operate on the same repository/worktree. A restart reconstructs the queue from SQLite and resumes only idempotent, checkpointed stages.

## Required persistent records

- `recovery_runs`: run ID, installation ID, start/last activity, status, current stage, checkpoint, progress, error.
- `source_accounts`: provider, non-secret account label, auth capability state, last successful sync.
- `conversation_sources`: provider/source ID, timestamp, project candidate, confidence, content hash, archive location, attachment references.
- `project_context`: project ID, current brief version/hash, decision sources, last validated time.
- `repository_snapshots`: local path, GitHub identity, branch/HEAD snapshots, dirty state, remote observation timestamp.
- `recovery_findings`: classification, evidence refs, rationale, proposed destination, validation state.
- `background_work_queue`: priority, stage, checkpoint, idempotency key, attempts, next retry, last error.

Secrets and provider tokens must remain in the existing local Vault/OS credential store. Never include them in reports, prompts, logs, Git remotes, or SQLite recovery records.

## First automatic workload after install

1. Snapshot all configured local roots and current Git state.
2. Inventory owned GitHub repositories and refs via local `gh` authentication.
3. Import every supported conversation source, starting with Zia and the providers already configured by the operator.
4. Generate a project/context map and identify missing sources.
5. Compare local and GitHub repositories/branches, including file-level differences.
6. Generate a recovery backlog ranked by risk, likely value, context confidence and effort.
7. Start only isolated, low-risk read-only analysis. No cross-project merge or product unification.

## Existing implementation to reuse

- `RepositoryLearningService`: incremental local repository inventory, SQLite cursor, project trees, redaction.
- `GitHubRepositoryPortfolio`: local/GitHub repository and branch inventory using host `gh`.
- `BranchRecoveryAnalyzer` from PR #303: local branch archaeology and unique-file/commit findings (pending its own CI validation).
- Existing conversation-recovery browser/provider components and durable task/message stores must be inspected and reused; do not build a second competing archive.
- `MissionEngine` and `SafeActionQueue`: foreground mission dispatch and durable work semantics.

## Acceptance gates

1. Cold install starts recovery automatically and reports its state in cockpit.
2. Restart resumes at the last durable checkpoint without duplicate imports.
3. A new foreground mission pauses recovery promptly and recovery resumes after it completes.
4. Provider outage does not lose other provider progress.
5. Dirty local files and untracked files survive discovery unchanged.
6. GitHub-only work remains recoverable after a local disk loss.
7. A full local/GitHub branch comparison identifies same-name SHA mismatches and unique commits.
8. Project context is versioned and source-linked before any legacy code is judged.
9. Candidate recovery happens only in a new isolated branch/worktree pinned to a SHA.
10. Tests, reviewer receipt and explicit operator approval are required before merge.

## Rollout sequence

A. Make current local repository learning start by default, with a safe disable switch and health/status visibility.
B. Add durable recovery supervisor and foreground pre-emption.
C. Integrate local Git + GitHub CLI snapshots and reports.
D. Integrate supported conversation ingestion and archive, including Zia after source capability is verified.
E. Context-grounded branch recovery proposals and isolated recovery worktrees.
F. Controlled Codex/Claude execution, independent review, and operator approval.

Each stage must have tests and a separate merge. The complete 24/7 capability must not be advertised until cold-start, pre-emption, restart recovery and source-ingestion E2E tests pass.
