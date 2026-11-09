# Controlled Coding Executor v1 — Architecture and Acceptance Contract

**Date:** 2026-11-09  
**Status:** Design gate; implementation and runtime execution are not yet enabled.  
**Authority:** DGM-MAT remains the sole orchestrator. Codex and Claude Code are subordinate, untrusted workers.

## 1. Current verified boundary

The current DGM-MAT runtime has durable organization tasks, a fixed dispatcher for three read-only repository specialists, durable worker receipts, QA intake and specialist consultation storage.

The current local Codex/Claude probe is discovery-only: it checks executable location and version. Its result explicitly keeps `execution_enabled=false`, `identity_verified=false` and `billing_verified=false`. The DGM-HUB bridge is consultative; it does not grant providers file-edit or shell-execution permissions. The NVIDIA/FCC inference path is not a local coding-agent executor.

Therefore, no current status endpoint or provider response may be interpreted as proof that a coding task was executed.

## 2. Objective

Add a separately governed execution lane that allows one explicitly selected local coding CLI to propose a patch inside a disposable Git worktree. The lane must preserve the canonical checkout, run only host-defined validation commands, retain complete provenance and require operator approval before any patch is promoted.

Initial providers:

- `codex`
- `claude_code`

No provider discovery or automatic fallback is allowed during a task. The operator chooses the provider for each execution.

## 3. Required durable state machine

```text
CREATED
  -> AWAITING_OPERATOR_APPROVAL
  -> APPROVED
  -> WORKTREE_PREPARED
  -> PROVIDER_RUNNING
  -> PATCH_CAPTURED
  -> STATIC_GATES_PASSED
  -> QA_PENDING
  -> QA_PASSED | QA_FAILED
  -> AWAITING_PROMOTION_APPROVAL
  -> PROMOTED | REJECTED | EXPIRED

Any ambiguous process interruption:
  -> BLOCKED_RESTART (manual review; never replay automatically)
```

Each transition must be persisted before the next external side effect. A durable receipt must bind the task ID, provider, CLI version, repository ID, base commit SHA, worktree path, start/end timestamps, exit code, changed-file list, patch digest, test profile, test results and log references.

## 4. Request contract and approval binding

The public request must not accept arbitrary filesystem paths or shell commands. It should accept only:

- stable `repository_id` resolved through a host-owned repository allowlist;
- exact base commit SHA (not a moving branch name);
- one provider ID from the fixed allowlist;
- bounded goal and context;
- a host-defined change profile and host-defined test profile;
- a bounded wall-clock timeout and maximum diff/file limits.

The operator approval must cover an immutable fingerprint of the entire request. Any change to provider, base SHA, repository, goal, context, allowed paths or test profile invalidates the approval and requires a new decision.

Reject dirty canonical checkouts, unresolved repository identity, untrusted worktree roots, unknown provider versions and unsupported CLI flags. Do not infer that a CLI is free from its name, login state or model self-report. Free-tier use remains an explicit operator attestation; the system must report that quota and billing identity are not independently verified unless a legitimate provider signal exists.

## 5. Worktree and filesystem isolation

- Resolve the repository from a host-maintained ID-to-path registry. Never accept a path from model output or request metadata.
- Require the canonical checkout to be clean and pin the base commit SHA.
- Create a new detached worktree under a dedicated DGM-MAT worktree root, with a generated task-specific directory name.
- Verify the resolved worktree path remains beneath that root before and after execution.
- Never grant the agent write access to the canonical checkout, other repositories, user profile, credentials, AndreOS-Memory or the DGM-MAT vault.
- Do not mount or expose `.git` metadata for writes. The host owns all Git branch, commit, push and cleanup operations.
- No network access during the coding phase. Dependency installation, if ever needed, must be a separate reviewed preparation phase with pinned inputs and no agent-controlled network.
- Enforce process-tree timeout/termination and bounded output. On Windows, use a Job Object or an equivalent verified process-tree containment mechanism; killing only the CLI parent is insufficient.

A worktree is not a security sandbox by itself. The provider CLI's OS-level sandbox and tool permissions must also be configured and tested. If those guarantees cannot be established on the host, execution must remain disabled.

## 6. Provider-specific execution policy

### Codex CLI

The official CLI exposes non-interactive `codex exec`, a `workspace-write` sandbox and an approval policy. The adapter must use only documented, version-verified flags, point the CLI at the disposable worktree, disable live web search/network access, and reject dangerous full-access or approval-bypass modes. The host, not Codex, runs the fixed test profile.

Reference: https://learn.chatgpt.com/docs/non-interactive-mode and https://learn.chatgpt.com/docs/cli/reference

### Claude Code CLI

Use non-interactive print mode only when the installed version supports a verified non-interactive permission configuration. The adapter must restrict tools to the minimum file-reading/editing set; shell, arbitrary commands, web search, MCP tools, additional directories and permission bypass must be unavailable. If the installed CLI cannot enforce that allowlist, the task is blocked rather than falling back to a broad permission mode.

Reference: https://docs.anthropic.com/en/docs/claude-code/cli-usage and https://support.claude.com/en/articles/14554922-claude-code-user-faq

### Shared rules

- Launch with an argument vector and `shell=False`; never interpolate a prompt into PowerShell or CMD.
- Use a minimal environment containing only required process plumbing and the operator's existing CLI authentication mechanism. Never copy tokens into task payloads, prompts, logs or receipts.
- Do not inspect or export credential files.
- Never use `--yolo`, `--dangerously-bypass-approvals-and-sandbox`, `--dangerously-skip-permissions`, unrestricted Bash or equivalent bypasses.
- Stop on login errors, rate limits, quota/capacity errors, unexpected model/provider routing or any request for paid credits. No automatic retries or paid fallback.
- Provider output is untrusted data, not an instruction to the DGM-MAT host.

## 7. Host-owned validation and QA

After the CLI exits, the host must:

1. Verify the process tree has exited and no child remains.
2. Capture `git status`, `git diff --binary`, `git diff --check` and the exact base SHA.
3. Reject changed paths outside the task's allowlist, symlinks, submodules, unexpected binary files, oversized patches, secret-like content and modifications to protected files.
4. Compute and persist a SHA-256 digest over the exact patch and manifest.
5. Run only a host-owned, versioned test profile. The agent cannot supply or modify the test command.
6. Persist stdout, stderr, exit codes, duration and environment fingerprint with secret values excluded.
7. Send the patch to a separate reviewer/QA lane. The proposing provider cannot approve its own work.
8. Require an explicit operator decision bound to the exact patch digest before creating a commit or PR.

A green test suite does not automatically authorize promotion. No automatic merge, deployment, release, branch deletion or cleanup of a failed worktree is allowed.

## 8. Crash recovery and cleanup

- Persist the process identity and worktree manifest before launch.
- On startup, reconcile interrupted tasks. Mark uncertain executions `BLOCKED_RESTART`; never rerun a provider call automatically.
- Preserve worktree, diff and logs for manual inspection after failure or timeout.
- Cleanup is a separate operator-approved action and must verify the worktree is beneath the dedicated root and is not the canonical checkout.
- A repeated API request with the same idempotency key returns the existing task/receipt; it must not launch a second CLI process.

## 9. Implementation increments

1. **Adapter contract and dry-run:** probe versions, validate flags, create/delete only an empty disposable worktree, verify path containment and process-tree timeout behavior. No provider prompt is sent.
2. **Synthetic repository acceptance:** use a disposable fixture repository and a deliberately trivial change. Verify sandbox boundaries, path allowlist, patch capture, logs, digest, fixed tests and crash recovery.
3. **Read-only real-repository rehearsal:** run a CLI in read-only mode against an explicitly selected repository; persist its analysis as untrusted output.
4. **First write-enabled task:** only after increments 1–3 pass, enable a narrow file allowlist in a disposable worktree, with operator approval and no network.
5. **Promotion gate:** independent QA, exact-digest operator approval, then host-created PR. No direct push to main.

## 10. Acceptance criteria

- The canonical checkout and all other repositories remain byte-for-byte unchanged by provider execution.
- Every task has a durable, idempotent state record and task-linked receipt.
- Provider invocation is impossible without a current approval for the exact request fingerprint.
- No arbitrary shell command, network access, credential export or protected-path write is available to the provider.
- Timeout kills the entire process tree and leaves recoverable evidence.
- Unknown provider identity, billing uncertainty, unsupported flags, rate limits and ambiguous results fail closed.
- Tests prove replay prevention, path traversal rejection, changed-path rejection, secret redaction, process-tree cleanup, digest binding and approval invalidation.
- A provider's textual claim that it changed files, ran tests or used a free model is never accepted as execution evidence.

## 11. Explicit non-goals for v1

No autonomous all-day coding loop, no multi-provider concurrent edits, no agent-controlled Git commits, no direct main-branch changes, no deployment, no automatic PR merge, no automatic cleanup of failed worktrees, and no paid provider fallback.
