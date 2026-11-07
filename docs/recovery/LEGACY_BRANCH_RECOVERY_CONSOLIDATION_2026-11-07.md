# Legacy branch recovery consolidation — 2026-11-07

## Scope and safety

This branch is based on the current `main` at the start of the recovery: `c009c512593f16ee1bf085012fa700e4352433fe`.

No legacy branch was deleted, rewritten, rebased, or modified. No recovered feature has been merged into `main`. The branch is intentionally a reviewable staging point.

## Recovery decisions

| Legacy branch | Decision | Evidence / reason |
|---|---|---|
| `feat/free-tier-browser-ai-consult-2026-11-05` | **Preserved in this branch, isolated / not activated** | The SQLite consultation queue, API router and store tests are not present in current `main`. They are copied as separate modules. The API router is deliberately NOT registered in current `api_server.py`: the branch does not contain a verified extension-side poll/send/result workflow, and the current browser operator is a different task/approval lane. The legacy API-server and security-policy files are preserved as clearly labelled archival snapshots, not as files to restore wholesale. |
| `feat/browser-recovery-deepseek-qwen-2026-11-06` | **Already superseded / no copy** | Current `main` already recognizes DeepSeek and Qwen routes and provider hosts. Current `browser_extension/content.js` is newer (676 lines vs 493 in the legacy branch), and current capture API tests cover five providers. The legacy branch's content script must not overwrite the newer implementation. |
| `feat/telescope-metadata-only-2026-11-03` | **Already integrated / no copy** | Current `main` contains `core/recovery/ai_source_inventory.py`, metadata-only `TelescopeAdapter`, the recovery API endpoint, inventory script and tests. The current adapter uses an explicit allowlist and avoids raw session detail payloads. |
| `feat/external-agent-readiness-probe-2026-11-03` | **Already integrated and evolved / no copy** | Current `main` contains `core/development/external_agent_probe.py` and the associated readiness API/security route. Current implementation includes additional safe-process handling and uses the existing local coding-agent probe for Codex. Replacing it with the older branch version would regress it. |
| `feat/browser-mission-queue-v1` | **Superseded / no copy** | The browser operator API and durable queue now exist in `main`. The extension background script and manifest have identical blob SHAs to current `main`; the installer PowerShell script also has the same blob SHA. The old popup's direct `DGM_SEND_MESSAGE` path bypassed the later server-side approval queue, so it was intentionally not recovered. Current `main` explicitly rejects direct content-script send requests and tests that bypass; approved sends use the server-governed browser operator. |

## Preserved free-tier consultation files

- `core/recovery/browser_consult_store.py`
- `core/api/browser_consult_api.py`
- `tests/test_browser_consult_store.py`
- `recovery/legacy-branch-snapshots/free-tier-browser-consult/core__api__api_server.py.legacy-snapshot.txt`
- `recovery/legacy-branch-snapshots/free-tier-browser-consult/core__api__security_policy.py.legacy-snapshot.txt`

The store is SQLite-backed and has explicit enablement and provider allowlisting, bounded prompts/responses, secret-pattern checks, cooldowns, idempotency, no automatic replay after ambiguous restart, and marks provider output as untrusted. The API uses the existing local audit writer.

## Security finding — legacy direct-send bypass

The old `feat/browser-mission-queue-v1` popup implemented a direct `chrome.tabs.sendMessage(... DGM_SEND_MESSAGE ...)` path after a local browser confirmation. That path did not use the current server-side approval queue. Current `main` has a negative test asserting that direct content-script sends are rejected, and the browser operator API requires a server-recorded approval. This legacy direct-send path is deliberately excluded and must not be revived.

## Archived integration hooks

The legacy branch also modified `core/api/api_server.py` and `core/api/security_policy.py` to register/classify the consultation routes. Their complete source snapshots are retained under `recovery/legacy-branch-snapshots/free-tier-browser-consult/`. They are intentionally not installed over current `main`, because those files have evolved since the legacy branch diverged. Their intended route registration/classification must be reconciled as a focused patch only after the extension workflow and tests exist.

## Required work before activation or merge

1. Add an extension-side consultation state machine that claims a consultation only for the matching allowlisted provider, previews/authorizes the send, sends through the visible UI only, captures the rendered answer, and reports result/block state. Do not reuse historical recovery capture to send prompts.
2. Add API integration tests for authentication scope, route classification, audit failure behavior, prompt release, result persistence, and unauthorized requests.
3. Add extension tests for explicit user approval, provider mismatch, quota/login/challenge stops, UI mismatch, interrupted session, duplicate delivery and no automatic retry.
4. Reconcile provider scope: this legacy queue supports ChatGPT, Gemini and Grok only. DeepSeek and Qwen remain in the separate five-provider browser operator/recovery lane until a compatible consultation adapter is implemented and tested.
5. Run focused Python and extension tests, the full relevant test suite, security negative tests, and Windows 10 end-to-end validation before enabling it. No runtime acceptance is claimed by this GitHub-only recovery.

## Validation status

- GitHub branch creation and file preservation: completed.
- File-level comparison against current `main`: completed for the candidate modules listed above.
- Automated tests executed in this recovery session: **none** (GitHub-only environment).
- Runtime/Windows/Chrome acceptance: **not performed**.
- Activation, merge and legacy branch deletion: **not performed**.

## Cleanup recommendation

All five audited source branch refs can be deleted after the owner verifies that PR #283 contains the recovered consultation modules and archival integration snapshots. Four branches are already superseded/integrated; the free-tier consultation branch's five changed files are represented in PR #283 as active isolated modules or labelled archival snapshots. Keep the new `recovery/legacy-branch-consolidation-2026-11-07` branch and PR #283 open. Deleting old branch refs does not require deleting their PR/commit history; preserve that history.
