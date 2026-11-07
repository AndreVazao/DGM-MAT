# Local Coding Agents and Operator-Adaptive Context

**Date:** 2026-11-06  
**Status:** Architecture proposal for review; PC acceptance pending Monday  
**Related:** #159, #211, #212, #237, #241, #242; PRs #220, #236, #238

## 1. Operator-confirmed target environment

The operator confirms that the following two local coding agents are configured through the local Free Cloud Code (FCC) server with NVIDIA NIM:

- Codex Free
- Claude Code Free

They are local CLI coding agents and must be treated as distinct execution backends. The DGM-MAT browser consultation providers remain ChatGPT, Grok, Gemini, DeepSeek and Qwen. Do not collapse these two lanes into one generic provider list.

The PC is offline until Monday 2026-11-09. Therefore the configuration above is an operator-provided current statement, not a live probe performed for this document. Historical readiness reports dated 2026-11-03 are diagnostic snapshots only and must not override this newer statement.

## 2. Three independent subsystems

### 2.1 Model inference

Existing model inference remains in the provider layer:

- Ollama is local and loopback-only; it has a free-RAM guard and must be skipped when the host is under pressure.
- The existing FCC NVIDIA provider is an HTTP model adapter, not a general-purpose CLI coding-agent executor.
- Provider registration remains explicit and disabled unless the runtime policy permits it.
- The model identity, provider, endpoint class, quota/cost evidence and request ID must be recorded separately. A configured provider is not proof of current availability, free quota or successful inference.

### 2.2 Coding-agent execution

Codex Free and Claude Code Free require a separate agent-execution contract. A model completion endpoint must never be presented as equivalent to a coding agent.

Each delegated task packet must contain:
- Stable task and mission IDs; project ID and repository identity.
- A bounded worktree path and base commit SHA.
- Objective, acceptance criteria, relevant files and evidence references.
- Explicit allowed operations and denied operations.
- Timeout, cancellation token, output budget and correlation ID.
- A minimal context packet; never attach the entire Vault by default.

Each result must contain:
- Agent ID, CLI version, backend/provider and model identity when observable.
- Start/end timestamps, exit status and cancellation/timeout state.
- Structured summary, changed paths, patch/diff reference and hashes.
- Commands/tests requested and actual results (the agent cannot self-certify tests it did not run).
- Warnings, unresolved questions and provenance.
- Explicit distinction between completed, partial, failed and unverified.

The DGM-MAT owns mission state, policy, worktree creation, backup, patch validation, test execution, QA and PR preparation. The external agent is an untrusted worker. Its proposed code is data until the DGM-MAT validates it.

### 2.3 Operator-adaptive context memory

The Vault and retrieval layer are the durable memory. A language model is optional assistance for extraction, classification, summarization or reranking; it is not the memory database and does not silently train its weights.

Store memory records with:
- Record ID, type, project/scope and normalized content.
- Source conversation/message/meeting/mission/file references.
- Created/observed timestamps and applicable time range.
- Evidence class: explicit operator instruction, confirmed operator decision, observed fact, validated lesson, agent proposal, inferred preference or unresolved hypothesis.
- Confidence, validation state, author/provider and extraction model/version.
- Supersedes/superseded-by links and review history.

Rules:
- Explicit operator corrections take precedence over inferred preferences.
- A proposal or majority vote never becomes an operator decision automatically.
- Conflicting records remain visible until resolved; do not silently overwrite.
- Retrieval is project-scoped by default. Cross-project reuse must not expose private project artefacts.
- Each context item injected into a task must carry its source reference and evidence class.
- The operator must be able to inspect, correct, supersede and request omission of a memory item.
- Private conversation bodies and Vault contents stay local by default. External context transmission requires a separate explicit task policy and data-minimization step.

## 3. Selecting a free context model

Do not hard-code a specific model before Monday's host check. The current PC has historically had very limited RAM, and prior small Ollama models were stopped due to weak performance. A model that is technically free but destabilizes the PC is not an acceptable default.

Implement a replaceable model interface and a deterministic retrieval fallback first. Candidate models must be benchmarked on the actual host for:
1. Portuguese (Portugal) comprehension and faithful preference extraction.
2. Structured JSON/schema adherence.
3. Long-context retrieval precision and resistance to invented details.
4. Latency, peak RAM and effect on DGM-MAT responsiveness.
5. Repeatability and ability to cite exact Vault source IDs.
6. Zero-cost operation and whether quota/endpoint conditions are observable.

Benchmark at least:
- No-LLM deterministic retrieval baseline.
- Available local Ollama models (only models actually installed).
- Any verified free FCC/NVIDIA model suitable for context tasks, without assuming the coding agents' selected backend is available as a generic API.

Choose the smallest model that measurably improves retrieval/extraction without harming host stability. Store the benchmark report and model identity. If none passes, use deterministic retrieval and defer semantic extraction.

## 4. Browser work and broad interaction

The five browser providers remain separate from the two local coding agents. The existing browser mission queue and Chrome extension are the intended visible-UI channel.

The desired capability set for authorized web workflows includes:
- Read visible page content and inspect page state.
- Navigate, open tabs and follow links.
- Click controls, type into fields and edit content.
- Upload and download files through normal page controls.
- Submit forms, send messages and complete multi-step workflows.
- Verify the resulting visible state and capture evidence.

Use typed actions and explicit per-origin capability grants. A broad capability set does not mean every action is automatically approved:

- Read/navigation can be enabled for explicitly paired origins.
- Write/edit/upload/submit requires an approved mission policy and audit record.
- Delete, publish, send external communications, alter account/security/billing settings, purchase, transfer funds, merge or release require a specific confirmation immediately before execution.
- Historical conversation recovery remains read-only and cannot send messages.
- Stop on login challenges, CAPTCHA/MFA, quota/rate-limit notices, unexpected paid UI or unsupported selectors. Never bypass them.
- No cookie/token/password extraction, hidden/private API calls, arbitrary page JavaScript, or false claims of completion.

Every browser action must record target origin, action type, mission/task ID, approval basis, visible precondition, timestamp, evidence and outcome. Distinguish attempted, completed, failed and unverified.

## 5. Local agent readiness and FCC checks

The current `core/development/external_agent_probe.py` provides read-only Claude Code/FCC readiness checks. It is not the execution bridge and does not currently prove a Codex task can run.

Monday's first operation must be observational:
1. Inspect FCC process ancestry, listener address and port. Require loopback-only binding before use.
2. Read only non-secret FCC status/config metadata. Never print masked or unmasked secrets.
3. Record selected provider/model and the exact free endpoint/quota evidence available.
4. Inspect Codex and Claude CLI versions and supported non-interactive status commands. Do not guess command syntax.
5. Verify each agent's authentication/backend without sending a prompt.
6. Confirm the CLI launches with tools disabled or in the narrowest safe mode for a no-write smoke test.
7. Preserve current config and logs before any proposed repair. Do not restart or rewrite FCC blindly.

If zero-cost status is ambiguous, do not execute model requests. A prior NIM catalog entry or a provider label containing "Free" is not sufficient proof of current quota/cost.

## 6. Execution lifecycle

The intended governed lifecycle is:

1. Mission approved by the operator or an already-approved policy.
2. DGM-MAT creates a fresh isolated worktree from a verified base SHA.
3. DGM-MAT builds a minimal context packet from Vault evidence.
4. The selected local agent receives only the task packet and bounded workspace.
5. Agent progress and output are captured with durable task correlation.
6. DGM-MAT validates every changed path, symlink/reparse-point boundary and base hash.
7. Backup-first patch application is performed by the DGM-MAT executor, not by an unrestricted model shell.
8. Tests run through a fixed allowlisted command registry owned by DGM-MAT.
9. Independent QA reviews the diff and evidence.
10. DGM-MAT prepares a branch/PR and checkpoint; no auto-merge.
11. Operator reviews promotion/merge and any destructive or external side effect.

On timeout or interruption, do not blindly replay an agent task that may have completed. Reconcile process state, worktree changes and durable checkpoints first.

## 7. Monday acceptance checklist

- [ ] Confirm the PC is available and capture the current DGM-MAT/Git state without modifying dirty worktrees.
- [ ] Verify FCC listener is loopback-only; preserve config before any repair.
- [ ] Verify current provider/model identity and zero-cost/quota evidence.
- [ ] Probe Codex Free and Claude Code Free independently.
- [ ] Run a no-write smoke task through each agent and record exact exit/result.
- [ ] Verify DGM-MAT can cancel a task and recover after restart.
- [ ] Verify agent output cannot write outside the isolated worktree.
- [ ] Benchmark the deterministic context baseline and installed candidate models under a RAM safety reserve.
- [ ] Verify retrieved preferences cite the source record and explicit corrections supersede older inferences.
- [ ] Test visible browser read, navigation, click, type, upload/download and submit flows on approved test targets; test confirmation gates for destructive/external actions.
- [ ] Produce an E2E report separating GitHub CI, mocked tests, live PC tests and blocked items.

## 8. Non-goals and permanent boundaries

- No paid API, subscription, credit purchase or silent paid fallback.
- No credential extraction or browser-profile scraping.
- No CAPTCHA/MFA or provider quota/rate-limit bypass.
- No unrestricted shell, admin elevation or arbitrary local filesystem access for external agents.
- No writes to the main checkout or real project repositories before governed worktree validation.
- No auto-merge, auto-delete, or irreversible self-modification.
- No claim of learning through model-weight training; adaptation means auditable memory, retrieval and validated policy updates.

## 9. Current implementation mapping

| Capability | Existing foundation | Remaining work |
|---|---|---|
| Five browser AIs | PR #236; issue #241 | Mission planner selection/synthesis and live provider acceptance |
| Browser history capture | PR #235; PR #239 | Live session acceptance; keep completeness conservative |
| Persistent Vault | PR #238; issue #237 | Review, merge sequencing, migration/restore acceptance |
| FCC/NIM model inference | `FccNvidiaProvider` | Current free quota and endpoint verification |
| Claude/FCC readiness | `external_agent_probe.py` | Current probe, Codex probe, safe CLI bridge |
| Codex Free task execution | Not confirmed in current main | Discover installed CLI contract and implement adapter |
| Governed patch executor | PR #220; issues #206/#212/#218 | Windows acceptance and MissionEngine integration |
| Execution learning | `LearningEngine`, `ValidatedLessonStore` | Operator preference/context store and retrieval |
| DGM-HUB collaboration | issue #159 and existing Hub bridge | Structured meeting memory and progressive leadership |

This document is an architecture and acceptance contract, not evidence that the listed future capabilities are already operational.

## Follow-up status — 2026-11-07

The implementation advanced after this checkpoint. Treat the following as the newer authoritative status for the affected workstreams:

- **Internal task lifecycle:** PRs #259, #260 and #261 are merged. MissionEngine uses the existing SQLite message bus for durable tasks, capability-aware delegation and a fixed typed dispatcher for the three read-only specialists. Task descriptions are never interpreted as commands. Worker messages carry task IDs and tasks complete only after a durable receipt.
- **Browser AI consultation:** PR #262 is merged. The supported visible-UI provider set is ChatGPT, Grok, Gemini, DeepSeek and Qwen. Direct task creation always requires explicit per-task approval. Mission-specific automatic send is permitted only while the server-verified parent checkpoint is RUNNING; the queue rechecks before claim. Old PRs #235, #236 and #239 were closed as superseded.
- **Persistent local Vault:** PR #263 is merged. Raw browser captures and redacted normalized conversations are stored separately; local progress and repository snapshots can be synchronized. Old PR #238 was closed as superseded. Provider oldest-boundary evidence remains deliberately unconfigured, so hash integrity is never treated as proof of complete conversation history.
- **Resource policy:** Vault startup bootstrap is opt-in and defaults OFF until the Windows host is measured. Manual synchronization is available via `scripts/sync_dgm_vault.py`.
- **Windows build:** PR #262 produced a validated `DGM-MAT-Windows-3.12-94923b7` artifact in run `42356491067`. PR #263 has a separate mainline Windows build in progress; the PR #262 artifact predates Vault integration and must not be represented as containing the Vault changes.
- **Local acceptance:** The operator PC remains offline until 2026-11-09. CI is not proof of installation, authenticated provider operation, task recovery on Windows, or performance on the legacy hardware.

Next gates:
1. Validate the post-PR-263 Windows executable and SHA-256.
2. Back up the existing installation and runtime before any replacement.
3. Measure actual CPU/RAM/disk, then test Vault migration and task/receipt recovery on the real host.
4. Configure the repository allowlist explicitly and validate all three read-only specialists against manual inspection.
5. Keep code mutation disabled until isolated worktree, approval-bound patch digest, independent QA and rollback are proven.
