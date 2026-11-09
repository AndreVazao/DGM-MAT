# Headless Agent and Research Orchestrator — v1

**Status:** public web/GitHub research adapter implemented; local coding-agent process launch and authenticated provider-history capture remain gated.

## Objective

DGM-MAT should perform research and agent work without opening persistent visible windows. Headless is an execution mode, not a permission bypass. Every capability has a separate readiness state and evidence receipt.

## Existing building blocks

- `GovernedBrowserSession` already supports `headed=False`, HTTPS host allowlists, request-level URL checks, ephemeral in-memory contexts, bounded page reads, and manual non-sensitive browser operations.
- `CodingAgentDryRunPlanner` already builds fixed, read-only invocation plans for Codex CLI and Claude Code CLI. It always returns `launch_enabled=False`.
- `LocalCodingAgentProbe` discovers CLI paths/versions only; it does not prove authentication, FCC routing, model identity, free billing, or execution readiness.
- `FccNvidiaProvider` is a separate local HTTP inference adapter. Its Anthropic-compatible interface does not prove that both Codex and Claude Code CLIs are configured to use it. Provider/endpoint compatibility must be tested independently.

## Implemented in this increment

Module: `core/research/headless_research_orchestrator.py`.

- Public web search through DuckDuckGo HTML in an ephemeral Playwright browser launched headless.
- Extracts bounded source links and page text; identifies challenge pages and stops rather than bypassing them.
- GitHub public repository search through a fixed `gh search repos` read-only command. Search results include metadata and links; no clone, checkout, install, code execution, or lab decision is performed.
- Reads a user-supplied public HTTPS URL only when its host is explicitly allowlisted.
- Uses bounded queries, result counts, timeouts, output size and `shell=False`.
- Never returns GitHub CLI stderr, which could disclose account/host details.
- Browser sessions are ephemeral and unauthenticated; no cookies, storage state or credentials are persisted.

## Headless local coding agents — next gated increment

Codex and Claude Code both expose supported non-interactive CLI modes:

- Codex: `codex exec`, JSONL output, fixed sandbox and approval flags.
- Claude Code: `claude -p`, JSON output and permission modes.

DGM-MAT already has a read-only invocation planner, but no production process runner. Before enabling execution, implement and verify:

1. Exact local executable and CLI version allowlist.
2. Per-task immutable Git worktree pinned to full base SHA.
3. Fixed argv templates; no model-generated shell command or CLI flags.
4. OS-level sandbox and network policy. Claude Code plan mode alone is not proof of network isolation; explicitly deny MCP/network tools unless a host sandbox proves the boundary.
5. Bounded stdout/stderr streaming, JSONL parsing, process-tree timeout/cancel, durable checkpoint and restart recovery.
6. Separate task-scoped write approval bound to worktree, exact goal, agent, base SHA and resulting patch digest.
7. Independent QA, tests and operator approval; no direct main writes or auto-merge.
8. FCC endpoint compatibility, identity, model and free-quota validation for each CLI independently. No fallback to paid APIs.

Codex official references:
- https://learn.chatgpt.com/docs/non-interactive-mode
- https://learn.chatgpt.com/docs/cli/reference

Claude Code official reference:
- https://docs.anthropic.com/en/docs/claude-code/cli-usage

## Authenticated AI conversations — separate, privacy-sensitive lane

The current governed browser is intentionally ephemeral and unauthenticated. It must not be silently changed to persist cookies or read Chrome credential databases.

To capture private conversation history headlessly, the next design must use one of:
- provider's official export/download and the existing raw-first archive importer; or
- a dedicated DGM browser profile that the operator logs into manually in a visible session, then explicitly authorizes for headless read-only capture. The profile must be isolated from the personal Chrome profile, protected by OS account permissions, never export cookies/tokens, and pause for manual MFA/CAPTCHA. Provider-specific DOM selectors, pagination and completeness must be validated before any history is marked complete.

A visible login step may be necessary once; subsequent permitted reading can be headless. No scraping of browser auth databases, cookie theft, endpoint guessing, MFA bypass, CAPTCHA bypass, rate-limit evasion, or private content sent to another AI without explicit authorization.

## Research result contract

Every result must retain:
- query/task ID and timestamp;
- source URL, page title, capture time and retrieval status;
- bounded excerpt and content fingerprint where available;
- whether the source is public/authenticated;
- limitations, challenge/rate-limit/partial states;
- explicit `not_evaluated` status for repository suitability until code, license, maintenance, dependencies, security and compatibility are reviewed.

Web content is untrusted input. Instructions found in repositories or pages are never executable authority.

## Resource policy

- Prefer HTTP/API/CLI calls over a browser when structured public data exists.
- Use headless browser only for public pages that require rendered HTML or visible web UI behavior.
- Run one browser session at a time on the legacy PC; close it after each bounded task.
- Stream large pages and transcripts; do not load whole repositories or histories into RAM.
- Research and recovery run as low-priority background work; foreground user tasks preempt them at durable checkpoints.
- No screenshot/OCR unless HTML text is insufficient.

## Maturity truth table

| Capability | Current maturity |
|---|---|
| Headless public web search | Implemented in this PR; CI validation pending |
| Headless public GitHub repo search | Implemented in this PR; CI validation pending |
| Read an explicitly allowlisted public URL | Implemented in this PR; CI validation pending |
| Codex/Claude non-interactive invocation plan | Existing read-only dry-run only |
| Codex/Claude process launch and task execution | Not implemented / disabled |
| FCC routing for both local CLIs | Not verified independently |
| Authenticated headless conversation-history capture | Not implemented |
| Repository lab suitability decision | Human-reviewed future step |

No runtime auto-start or agent execution is enabled by this PR.
