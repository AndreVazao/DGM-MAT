# PC Setup, Path Registry and Reprovisioning Inventory
Date: 2026-10-11
Status: first evidence-backed snapshot; not a complete machine inventory.

## Purpose
Keep a reproducible, auditable record of the Windows workstation and provide DGM-MAT with a governed way to discover tools, resolve paths, compare requirements with reality, and prepare an approved rebuild on another PC. Hardware observations describe this workstation only; they must never become permanent architecture limits.

## Evidence snapshot
Collected from PC-Vazao-Anjos before Desktop Commander usage reached 0%:
- Windows 10 Home, build 19045, x64.
- Intel Pentium Dual CPU T3200 @ 2.00 GHz; 2 cores / 2 logical processors.
- Approximately 2.96 GiB RAM.
- Workspace: `C:\\ProgramasGodMode`.
- DGM-MAT working repository: `C:\\ProgramasGodMode\\DGM-MAT`; observed branch `feat/conversation-turn-semantics-v1`.
- Runtime target: `C:\\DevopGodMode`.
- Active memory checkout: `C:\\AndreOS-Memory`; remote source of truth: `AndreVazao/andreos-memory`, branch `main`.
- Legacy memory archive: `C:\\AndreOS-Memory-LEGACY-2026-10-07`; preserve as read-only archive.
- `C:\\ProgramasGodMode\\DGM-MAT-FULL-MIRROR` and its GitHub repository are historical read-only material; do not alter.
- Python 3.12.6: `%LOCALAPPDATA%\\Programs\\Python\\Python312\\python.exe`; launcher `C:\\Windows\\py.exe`.
- Node.js 24.20.0 / npm 11.19.0: `C:\\Program Files\\nodejs`.
- Git 2.45.1.windows.1: `C:\\Program Files\\Git\\cmd\\git.exe`; Git Bash `C:\\Program Files\\Git\\bin\\bash.exe`.
- Ollama 0.23.0: `%LOCALAPPDATA%\\Programs\\Ollama\\ollama.exe`; API responded at `http://127.0.0.1:11434`.
- Observed Ollama models: `qwen2.5:1.5b`, `qwen2.5-coder:1.5b`, `llama3.2:1b`, `deepseek-r1:1.5b`.
- VS Code command: `%LOCALAPPDATA%\\Programs\\Microsoft VS Code\\bin\\code.cmd`; version not captured.
- WinGet 1.28.240; Chocolatey command at `C:\\ProgramData\\chocolatey\\bin\\choco.exe`; version not captured.
- FCC executable observed at `%USERPROFILE%\\.local\\bin\\fcc-server.exe`; workspace `C:\\ProgramasGodMode\\ClaudeCode-Dashboard`. Its full health/provider path has not been verified end-to-end.
- FCC-managed Python environment observed under `%APPDATA%\\uv\\tools\\free-claude-code`; uv Python under `%APPDATA%\\uv\\python\\...`. Exact versions remain to be captured.
- DGM-MAT Core health endpoint previously returned HTTP 200 at `http://127.0.0.1:8181/health`.
- Sovereign Trader venv observed at `C:\\ProgramasGodMode\\VazaoSovereignTrader\\PC_ENGINE\\.venv`.
- NVIDIA NIM was previously reported as configured, but current credentials, quotas, and end-to-end health are unverified.

This is a dated snapshot, not proof that every listed process remains running. A missing registry display-name match is not proof that a tool is absent. Desktop Commander currently reports 0% calls remaining, so no further local scan or local-to-remote Git reconciliation can be claimed in this checkpoint.

## Required canonical records
Maintain separate version-controlled records for:
1. Machine observations (timestamped, host-specific, never treated as universal requirements).
2. Tool catalogue (stable ID, purpose, publisher, official source/package ID, detected version, path, architecture, signature/hash evidence, licence/cost/quota, permissions, project scope, install/check commands, rollback, last verification).
3. Project dependency manifests (required, optional, conditional; minimum/maximum tested versions; compatibility notes).
4. Bootstrap/reprovision manifest (ordered prerequisites, detection probes, approvals, install plan, health checks, rollback/resume state).
5. Path alias registry (logical tool ID -> verified executable, working directory, configuration root, data root, API endpoint, discovery evidence and last-seen time).

## Path discovery and repair contract
- Resolve paths using evidence in this order: running process executable path; verified package-manager metadata; Windows App Paths / uninstall registry; known user install locations; PATH command resolution; repository and virtual-environment manifests; finally bounded read-only filesystem search.
- Record every candidate, its evidence and confidence. Do not silently pick a path where candidates conflict.
- Validate existence, executable identity/version, architecture, working directory, required adjacent files, and a harmless health/version probe.
- Prefer stable logical IDs and environment variables over hard-coded absolute paths. Store machine-specific resolved paths outside portable defaults and refresh them on each machine.
- Before changing a path, show old value, proposed value, evidence, affected callers/imports/shortcuts/services/tasks, backup location and rollback. Search references and test callers before applying.
- Do not rewrite user data, project files, PATH, registry, scheduled tasks, services or environment variables automatically without explicit approval.
- Never infer that a tool is safe merely because it exists. Apply project scopes, permissions, approval gates and provider health checks.

## Reprovisioning safety contract
- Discovery first; prepare a diff and request explicit approval before installs/upgrades/removals, elevated changes, licences, network access, permissions, credentials or any paid usage.
- Use official trusted sources; verify publisher/signature/hash when available; capture exit codes and redacted logs.
- Idempotent, resumable installation; back up config before migration; do not overwrite existing user data blindly.
- Adapt concurrency and model selection to measured available RAM/CPU/GPU, but keep capabilities available on stronger future machines. The present 2-core / ~2.96-GiB machine is not a permanent cap.
- Secrets only through an explicitly approved OS vault / credential manager / DPAPI-backed integration. Never store tokens, passwords, cookies or API keys in manifests, logs, Git, command lines or plain-text memory.
- Keep project data and credentials isolated by scope; no cross-project write access by default.

## PC dashboard and security gate
The next operational priority is the local PC cockpit, before phone pairing. The Core was previously observed on loopback port 8181, but the newer global authentication middleware was not confirmed active in the live process. Therefore do not expose the API on LAN, Tailscale, a public proxy or Vercel until a controlled restart and negative/positive HTTP + WebSocket tests prove authentication, scopes, revocation, anti-replay and CORS behavior. Prefer loopback-only operation until then. Do not auto-retry old queued missions or mutate historical mission records during recovery.

## Git and automation guardrails
- Do not modify the historical FULL-MIRROR.
- No GitHub Actions builds or workflow reruns by default; conserve minutes. Any future build workflow should be explicitly/manual triggered unless a separately approved critical need exists.
- A documentation branch is not the same as syncing the working PC. Local modifications, dirty files, branch divergence and tests must be reconciled when PC access returns; never force-push or overwrite unreviewed work.
- Do not claim a downloadable EXE exists until an actual, verified release artifact has been produced and linked.
- Current documentation branch: `continuity/pc-setup-2026-10-11`. This checkpoint intentionally changes documentation only.
