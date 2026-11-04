# Bounded Worktree Execution Safety

Date: 2026-11-04
Branch: feat/bounded-worktree-execution-2026-11-04
Base: origin/main (15bb570)

## Purpose

Repair the existing development execution primitives before any integration with the durable mission queue. This change does not enable a general-purpose autonomous coding agent.

## Worktree lifecycle

- Worktree names and task IDs are restricted to a conservative identifier format.
- A sandbox is a registered Git worktree created from a verified commit.
- Worktree roots are verified against Git's registered worktree list.
- Cleanup removes only worktrees with no tracked, untracked, or ignored content. Any recoverable data is preserved for human review.
- Sandbox paths are resolved under a configured worktree directory.
- Validation commands are a fixed catalogue: pytest against one explicit Python file below `tests/`. The runner disables bytecode and pytest cache writes to keep successful worktrees clean; compile checks remain in CI.
- Arbitrary shell strings, `python -c`, pip, and unlisted executables are rejected.
- Commands use `shell=False`, explicit working directory, timeout and streamed per-channel output caps.
- Validation uses the current Python interpreter and a minimal OS-only environment; provider/API credentials and arbitrary parent-process environment variables are not inherited.
- `IsolatedRuntime` is now only a compatibility adapter over this catalogue; it has no temporary-directory fallback and cannot run arbitrary argument lists.

## Patch application boundary

Patch application is deliberately outside this change. The separate PR #182
(feat/isolated-patch-apply-guard-2026-11-04) owns the explicit-target
SafePatchEngine.apply_patch guard. This branch does not weaken or replace it.

## Supervisor and executor

- Task metadata must include a valid ID and non-empty goal/description/summary.
- Caller-supplied shell, command, script, executable and argv fields are rejected.
- Approval requests persist risk score and impact through the existing ApprovalManager/SafeActionQueue facade.
- A generated diff already exists in its worktree; the executor no longer tries to re-apply that diff to the primary checkout.
- An empty diff is not reported as successful implementation; even a prepared diff is not reported as a completed task until independent QA and explicit integration occur.
- Dirty worktrees are preserved by cleanup refusal.

## Explicit limitations

- A Git worktree is repository isolation, not an OS-level security sandbox. A validation timeout terminates the direct child process; process-tree containment is not provided.
- Running tests executes repository code. This patch does not provide network isolation, resource quotas at OS level, or protection against malicious tests.
- The existing autonomous implementation stage is still a placeholder; no provider currently supplies code-generation output to this executor.
- This PR is not registered as a SafeActionQueue mission handler and does not modify runtime queue state.
- Human review and existing approval gates remain required before primary-branch integration.
