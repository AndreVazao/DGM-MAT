# Local coding-agent readiness probe v1

**Status:** Read-only discovery implemented; task execution deliberately disabled  
**Agents:** Codex CLI and Claude Code CLI  
**Parent issue:** https://github.com/AndreVazao/DGM-MAT/issues/242

## Separation of lanes

- Codex and Claude Code are local CLI coding agents. They are not browser providers and are not the same as the FCC/NVIDIA NIM HTTP inference provider.
- ChatGPT, Grok, Gemini, DeepSeek and Qwen remain visible-UI browser consultation providers.
- `FccNvidiaProvider` is a separate loopback HTTP inference adapter with its own free-tier budget controls.

## Implemented probe

`LocalCodingAgentProbe` recognizes only two fixed agent IDs:
- `codex` → `codex`, `codex.exe`, `codex.ps1`, `codex.cmd`
- `claude_code` → `claude`, `claude.exe`, `claude.ps1`, `claude.cmd`

On Windows, the probe checks the standard `%APPDATA%\\npm` shims first. PowerShell wrappers run only through `powershell.exe`/`pwsh` with `-NoProfile -NonInteractive`; command wrappers use `cmd.exe /d /c` with the fixed `--version` argument. If a safe interpreter is unavailable, the probe fails closed.

For each installed CLI it runs only `--version`, with:
- a bounded timeout;
- `shell=False`;
- a temporary working directory;
- a minimal environment containing process plumbing only;
- bounded/sanitized version output;
- no arbitrary command, executable path, argument list or prompt accepted from a task;
- no reading of credential files or secret environment values.

It records only the presence of selected endpoint environment variable names, never their values. A discovered CLI is not proof of provider identity, FCC routing, model identity, free billing or quota status.

MissionEngine exposes `probe_local_coding_agents()` as a read-only readiness operation. The office roster now declares `agent:codex-cli` and `agent:claude-code-cli` as OFFLINE, read-only roles with no repository write permission. They do not have execution handlers. The probe does not start a coding task or enable either role.

## Explicitly not enabled

- No Codex or Claude Code task execution.
- No arbitrary subprocess invocation.
- No prompt submission or source-file modification.
- No credential/config file parsing.
- No automatic fallback to paid APIs.
- No assertion that the installed CLI is connected to FCC/NVIDIA NIM or using a free model.

## Monday host acceptance

On the operator PC:
1. Run the read-only probe and record CLI paths/versions.
2. Independently verify the CLI's configured endpoint and selected model through its official local status/config UI, without reading or copying secrets into DGM-MAT.
3. Verify the FCC loopback listener and the actual route/model identity; record only safe endpoint metadata and status.
4. Verify the free quota/billing mode through authoritative local/provider status; unknown remains blocked.
5. Confirm the CLI can operate in a task-specific Git worktree and cannot access the primary checkout or protected directories.
6. Test cancellation, timeout, process interruption and result recovery with deterministic sample tasks.
7. Only then add explicit command builders for bounded plan/review tasks, followed by a separate implementation adapter behind the approval manager and backup-first executor.

## Permission contract for the future adapter

- Fixed executable identity and fixed command templates; no arbitrary arguments from model output.
- One task-specific worktree, no primary-checkout writes.
- Read-only planning/review mode by default.
- Implementation only after a task-specific approval referencing the exact task, worktree and patch digest.
- Output captured as bounded structured result and diff; no secrets or full environment persisted.
- Timeout/cancel kills the process tree and leaves worktree/outputs for recovery; never silently deletes dirty work.
- Independent QA/review must be a separate agent/role from the authoring CLI.

The probe is a discovery prerequisite, not permission to execute code.

## Unified operator readiness endpoint

The existing operator-only `GET /governance/agents/readiness` endpoint now reports both lanes without conflating them:
- `fcc_inference_ready` / `execution_scope=fcc_inference_only` describe only the verified loopback FCC inference route and exact allowlisted free NVIDIA NIM endpoint.
- `local_coding_agents.codex_cli` reports Codex executable/version presence only.
- `local_coding_agents.claude_code_cli` reports Claude Code authentication status through its fixed auth-status command.
- `local_coding_agents.execution_ready` and `local_coding_agents_execution_ready` remain false until host-validated worktree adapters and approvals exist.

No model request is made by the readiness endpoint. A positive FCC inference status is not permission to execute a Codex/Claude coding task.
