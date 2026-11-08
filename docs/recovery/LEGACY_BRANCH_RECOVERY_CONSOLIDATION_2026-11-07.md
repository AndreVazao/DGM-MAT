# Legacy branch recovery consolidation — 2026-11-07

## Scope and safety

This branch is based on the current `main` at the start of the recovery: `c009c512593f16ee1bf085012fa700e4352433fe`.

No legacy branch was deleted, rewritten, rebased, or modified. No recovered feature has been merged into `main`. The branch is intentionally a reviewable staging point.

## Recovery decisions

| Legacy branch | Decision | Evidence / reason |
|---|---|---|
| `feat/free-tier-browser-ai-consult-2026-11-05` | **Recovered in PR #283; isolated / not activated** | The SQLite consultation queue, API router and store tests were recovered. The router is registered in `api_server.py`, and the new paths are classified in `security_policy.py`. Legacy integration files remain archival snapshots only; they are not restored wholesale. |
| `feat/browser-recovery-deepseek-qwen-2026-11-06` | **Already superseded / no copy** | Current `main` already recognizes DeepSeek and Qwen routes and provider hosts. Current `browser_extension/content.js` is newer (676 lines vs 493 in the legacy branch), and current capture API tests cover five providers. The legacy branch's content script must not overwrite the newer implementation. |
| `feat/telescope-metadata-only-2026-11-03` | **Already integrated / no copy** | Current `main` contains `core/recovery/ai_source_inventory.py`, metadata-only `TelescopeAdapter`, the recovery API endpoint, inventory script and tests. The current adapter uses an explicit allowlist and avoids raw session detail payloads. |
| `feat/external-agent-readiness-probe-2026-11-03` | **Already integrated and evolved / no copy** | Current `main` contains `core/development/external_agent_probe.py` and the associated readiness API/security route. Current implementation includes additional safe-process handling and uses the existing local coding-agent probe for Codex. Replacing it with the older branch version would regress it. |
| `feat/browser-mission-queue-v1` | **Superseded / no copy** | The browser operator API and durable queue now exist in `main`. The extension background script and manifest have identical blob SHAs to current `main`; the installer PowerShell script also has the same blob SHA. The old popup's direct `DGM_SEND_MESSAGE` path bypassed the later server-side approval queue, so it was intentionally not recovered. Current `main` explicitly rejects direct content-script send requests and tests that bypass; approved sends use the server-governed browser operator. |

## Preserved free-tier consultation files

- `core/recovery/browser_consult_store.py`
- `core/api/browser_consult_api.py`
- `tests/test_browser_consult_store.py`
- `tests/api/test_browser_consult_api.py`
- `recovery/legacy-branch-snapshots/free-tier-browser-consult/core__api__api_server.py.legacy-snapshot.txt`
- `recovery/legacy-branch-snapshots/free-tier-browser-consult/core__api__security_policy.py.legacy-snapshot.txt`

The store is SQLite-backed and has explicit enablement and a five-provider allowlist (ChatGPT, Grok, Gemini, DeepSeek and Qwen), bounded/redacted prompts and responses, secret-pattern checks, cooldowns, idempotency while awaiting approval, one-time claim tokens, no automatic replay after ambiguous restart, and marks provider output as untrusted. The API uses the existing local audit writer and local-session authentication.

## Security finding — legacy direct-send bypass

The old `feat/browser-mission-queue-v1` popup implemented a direct `chrome.tabs.sendMessage(... DGM_SEND_MESSAGE ...)` path after a local browser confirmation. That path did not use the current server-side approval queue. Current `main` has a negative test asserting that direct content-script sends are rejected, and the browser operator API requires a server-recorded approval. This legacy direct-send path is deliberately excluded and must not be revived.

## Historical integration snapshots

The complete legacy versions of `core/api/api_server.py` and `core/api/security_policy.py` remain under `recovery/legacy-branch-snapshots/free-tier-browser-consult/` for provenance. The current branch has already reconciled the required changes as focused patches: `api_server.py` registers `browser_consult_router`, and `security_policy.py` classifies status/enqueue/approve as `OPERATOR` and next/result/block as `BROWSER_CAPTURE`. Do not restore the archived files wholesale.

## Implementation progress in this recovery PR

- Added explicit `PENDING_APPROVAL` state and per-request popup approval. The paired extension uses the dedicated `browser-consult-control` scope for status/enqueue/approve and `browser-capture` for claim/result/block; it never receives general `operator` scope.
- Added local-session authentication and explicit route classifications: enqueue/status/approve require the dedicated `browser-consult-control` scope; claim/result/block require `browser-capture`. The paired extension receives only these two narrow scopes, never general `operator`.
- Added a cryptographically random one-time claim token; result/block operations must present the matching token, which is cleared on completion or block.
- Added five-provider support and an opt-in extension polling toggle (disabled by default). The extension uses the already-tested visible-UI browser task executor and existing authenticated provider tabs; it does not use provider APIs or hidden endpoints.
- Added a popup form to create a consultation, explicitly attest free-tier account status, review pending requests, and approve each send. Each provider request remains separately approved.
- Added an optional AutoHelp fallback: only when the DGM-HUB has no ready free provider, and only when browser-consult, AutoHelp browser-consult and free-capacity environment opt-ins are enabled, AutoHelp queues a consultation for the five browser providers and records `WAITING_FOR_OPERATOR_APPROVAL`. No message is sent at enqueue time. Completed answers are appended to the linked local mobile thread as untrusted external suggestions.
- On extension service-worker restart, any persisted in-flight consultation claim is blocked as interrupted and cleared without replay, even if polling has since been disabled.
- Serialized consultation polling against mission browser execution so both cannot send concurrently in the same provider tab.
- Added API tests for route scopes, authentication, explicit approval, free-capacity attestation, claim ownership, untrusted result persistence and fail-closed audit errors on approval/prompt release; expanded store tests for approval, deduplication, secret blocking, restart handling and claim tokens.

## Remaining validation before activation/merge

1. Run focused Python tests for the consultation store/API and the existing five-provider browser extension tests.
2. Run the full relevant test suite, security negative tests, JavaScript syntax checks and extension packaging/build.
3. Verify audit-write failure behavior, worker restart during an in-flight browser send, stale claim rejection, popup UX and provider UI mismatch handling.
4. Perform Windows 10 + Chrome end-to-end acceptance using only free-tier accounts and a single manually approved test request per provider.
5. Keep `DGM_BROWSER_CONSULT_ENABLED=0` until those checks pass. The extension toggle is also opt-in and defaults off. No runtime acceptance is claimed by this GitHub-only session.

## Validation status

- GitHub branch creation and file preservation: completed.
- File-level comparison against current `main`: completed for the candidate modules listed above.
- Optional mobile AutoHelp-to-browser-consult handoff: implemented, gated by three explicit environment settings, and covered by a focused regression test.
- Browser extension worker restart recovery: stale one-shot claims are blocked and never replayed.
- Local automated tests executed in this recovery session: **none** (GitHub-only environment).
- GitHub Actions Focused PR Validation #716: **SUCCESS** (run `42475905963`).
- GitHub Actions Chrome Extension Validation #308: **SUCCESS** (run `42475905965`).
- Windows Executable Build #300: **SUCCESS** (run `42475905948`), incluindo deep executable check, final assertions e upload do artefacto.
- Artefacto atual: `DGM-MAT-Windows-3.12-54e344e`, 111,238,946 bytes; digest SHA-256 do arquivo GitHub `f5d5abefe05dd14c40043484f4601eb90cdcad45ae034d31d71fd2eb7eee97d2`; expira em 2027-02-06 11:28:39 UTC. O digest identifica o arquivo de artefacto, não o EXE.
- Check Snyk: **ERROR por quota esgotada** (“You have used your limit of private tests”); não há aprovação Snyk.
- Execução Windows: https://github.com/AndreVazao/DGM-MAT/actions/runs/42475905948
- Runtime/Windows 10/Chrome acceptance with real free-tier accounts: **not performed**.
- Activation, merge and legacy branch deletion: **not performed**. The feature remains disabled by default.

## Cleanup recommendation

All five audited source branch refs can be deleted after the owner verifies that PR #283 contains the recovered consultation modules and archival integration snapshots. Four branches are already superseded/integrated; the free-tier consultation branch's five changed files are represented in PR #283 as active isolated modules or labelled archival snapshots. Keep the new `recovery/legacy-branch-consolidation-2026-11-07` branch and PR #283 open. Deleting old branch refs does not require deleting their PR/commit history; preserve that history.


## Final CI and artifact update — 2026-11-07 21:29 UTC

This section supersedes the interim workflow numbers above.

- Validated head: `6be93325a8499683c39a360d58332cd367be95f1`.
- Focused PR Validation **#703: SUCCESS**.
- Chrome Extension Validation **#295: SUCCESS**.
- Windows Executable Build **#287: SUCCESS**. Its job completed every step successfully, including installer validation, executable deep check, final build assertions and artifact upload.
- Windows artifact: `DGM-MAT-Windows-3.12-eeaaec3`, 111,239,254 bytes.
- Artifact SHA-256: `3467d141ca2b9f2ad6220609ce527b8de5913e78381fe5f732c4f2a6f760aaf6`.
- Artifact expires: 2027-02-05 21:24 UTC.
- GitHub Actions result is green on the exact PR head. This is CI/build evidence only; Windows 10 installation, startup, browser extension pairing and real provider E2E remain untested on the owner's PC.
- PR #283 remains open and unmerged. All five source branches remain untouched.
- Activation flags remain off by default; do not enable production use until local acceptance.


## Scope correction and validation — 2026-11-08

A security review found that the original paired extension token had only `browser-capture`, while the popup also called status/enqueue/approve routes classified as `operator`; these calls would be rejected with HTTP 403. Corrected with the narrow `browser-consult-control` scope, without granting general operator authority. Both `/auth/session` and `/auth/pair` issue the extension session with exactly `browser-capture` and `browser-consult-control`.

- Integrated regression: paired extension session can read consultation status, enqueue and approve a consultation, while a general operator route still returns HTTP 403.
- Focused PR Validation #721: SUCCESS (run `42500111864`), 30 tests passed.
- Chrome Extension Validation #314: SUCCESS (run `42500577041`), 77 browser/API regressions passed; JavaScript fixtures, manifest, Bandit and focused `pip-audit` passed; no known vulnerabilities found in the dependencies audited by that workflow.
- Focused PR Validation #722: SUCCESS (run `42500577087`), including the updated pairing-scope expectation.
- Windows Build #305: SUCCESS (run `42500111911`), artefact `DGM-MAT-Windows-3.12-58b8cfc` (111,238,999 bytes; GitHub artefact digest `aa8d06ce803faa54ea01e5672d01726c1803a7b838a43331d86595d11e1f47cc`; expires 2027-02-06 16:29:08 UTC).
- Snyk remains unavailable because the private-test quota is exhausted; this is not a clean Snyk result.
- Head `c10d2a3` altera a expectativa de teste de emparelhamento, sem alterar o runtime relativamente ao commit `739edfc`.
