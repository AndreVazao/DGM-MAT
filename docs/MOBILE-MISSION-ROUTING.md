# Mobile conversation to mission routing

**Status:** implementation branch; not yet promoted to the active DGM-MAT runtime.

## Purpose

The mobile/Hub conversation service must not create a mission merely because a lightweight language classifier recognizes words such as "audit", "repair", "implement" or "sync". Mission creation is now gated by the authoritative `classify_mission_intent` decision used by the mission engine itself.

This prevents unsupported requests from accumulating as queued actions and prevents the conversation layer from implying that an operation is running when no registered handler exists.

## Supported requests

| User request | Mission intent | Execution policy |
|---|---|---|
| List repositories | `list_repositories` | Read-only allowlist; auto-approved |
| Summarize project architecture | `architecture_summary` | Read-only allowlist; auto-approved |
| Repository/Git status | `repository_status` | Read-only allowlist; auto-approved |
| Audit/analyze local repository or code | `local_research` | Read-only allowlist; auto-approved |
| PC or DGM-MAT status | `system_summary` | Read-only allowlist; auto-approved |
| Active engine inventory | `engines_inventory` | Read-only allowlist; auto-approved |
| Ollama status | `ollama_status` | Read-only allowlist; auto-approved |
| Claude status | `claude_status` | Read-only allowlist; auto-approved |
| Sync GitHub main into an isolated worktree | `repository_sync_worktree` | Supported, but requires operator approval |

Local audit/research is recognized only when the request names a local target (repository, project, code, docs, workspace or DGM-MAT) and contains no mutating intent. A mixed request such as "audit the repository and fix the code" is rejected as unsupported; it is not split into an automatically executable read-only portion.

## Unsupported requests

Until a real handler and tests exist, the mobile service does not create a mission for generic repair, implementation, deployment, external web research, or persistent-memory writes.

For these requests:
- the user message remains in the durable conversation thread;
- no mission is created;
- no queue action is created;
- no command, file write, Git operation or external research is started;
- the assistant explicitly reports that no executor is registered and that no action was performed.

The lightweight intent layer also marks repair, implementation, synchronization, deployment and destructive language as requiring approval. This is an additional safety signal; the mission router remains authoritative for deciding whether a registered handler exists.

## Mission status returned to the conversation

When a supported mission is created, the mobile response now includes:
- mission intent decision and support reason;
- mission ID and initial mission status;
- action queue status, when available;
- whether operator approval is required.

The assistant response distinguishes:
- `APPROVED`: dispatched by the read-only allowlist or explicitly approved by an operator;
- `RUNNING`: worker has started;
- `COMPLETED`: queue action ended, but the persisted mission result must still be inspected;
- `FAILED`: execution failed and must not be reported as success;
- `QUEUED`: awaiting approval; no action has run.

The runtime's existing queue consumer processes approved actions only. The conversation service does not mark a mission complete based solely on its creation.

## Current limits

There is still no generic code-editing executor. Repair/implementation tasks must remain blocked until a bounded executor is registered, tested in an isolated worktree, and connected to the approval/QA flow. The current local inference path is also memory-gated; on the present PC the deterministic response fallback is used.

## Validation

Focused validation covers the mobile conversation service, mission-intent router, read-only diagnostic missions and terminal mission-result guard. No production mission was created during these tests, and the active DGM-MAT service was not restarted.
