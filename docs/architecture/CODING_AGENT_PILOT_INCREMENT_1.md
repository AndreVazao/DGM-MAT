# Local coding-agent pilot — increment 1

**Status:** Dry-run invocation planner implemented; process launch remains disabled.

This increment creates a deterministic, approval-fingerprint-bound invocation plan for the two fixed local CLI identities. It deliberately does not launch either process, create a worktree, or write source files.

## What is enforced

- Repository IDs resolve only through a host-owned allowlist.
- The supplied repository path must exactly match the allowlisted canonical checkout.
- The worktree root must be separate from the canonical checkout.
- Base revisions must be full immutable Git object IDs.
- Provider IDs are limited to `codex` and `claude_code`.
- Goals, CLI version strings and turn budgets are bounded.
- Provider arguments are constructed internally; callers cannot supply shell commands or arbitrary CLI flags.
- Both invocation templates are read-only and disable writes in the plan contract. Codex also ignores user config; Claude network isolation is explicitly marked unverified and cannot be launched until a host-level network sandbox is proven.
- The request fingerprint binds provider, repository, base SHA, goal, CLI version, argv and permissions.
- The planner always returns `launch_enabled=false`.

## Provider command policy

Codex uses non-interactive `codex exec` with `--sandbox read-only`, `--ask-for-approval never` and `--ephemeral`. Claude Code uses print mode, plan permission mode and an explicit deny list for Bash, WebSearch and WebFetch. Plan mode is not an OS-level network sandbox; user/project MCP configuration may also exist. Therefore its network isolation is recorded as unknown, not false, and process launch remains disabled until a host-level sandbox and MCP-deny policy are verified.

References:
- https://learn.chatgpt.com/docs/non-interactive-mode
- https://docs.anthropic.com/en/docs/claude-code/cli-usage

## Next gates

1. Validate both exact command templates against the operator PC's installed CLI versions, without submitting a task prompt.
2. Add process-tree containment and bounded output capture.
3. Run a read-only synthetic-repository task and persist a durable receipt.
4. Only then implement a separate, per-task approved write-enabled worktree adapter.
5. Independent QA and operator approval remain mandatory before any patch promotion.

This is not yet a coding executor and must not be reported as one. In particular, Claude Code is not treated as network-isolated merely because it is in plan mode.
