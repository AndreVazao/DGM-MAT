# Legacy branch recovery consolidation — 2026-11-07

## Scope and safety

This branch is based on the current `main` at the start of the recovery: `c009c512593f16ee1bf085012fa700e4352433fe`.

No legacy branch was deleted, rewritten, rebased, or modified. No recovered feature has been merged into `main`. The branch is intentionally a reviewable staging point.

## Recovery decisions

| Legacy branch | Decision | Evidence / reason |
|---|---|---|
| `feat/free-tier-browser-ai-consult-2026-11-05` | **Preserved in this branch, isolated / not activated** | The SQLite consultation queue, API router and store tests are not present in current `main`. They are copied as separate modules. The API router is deliberately NOT registered in `api_server.py`: the branch does not contain a verified extension-side poll/send/result workflow, and the current browser operator is a different task/approval lane. |
| `feat/browser-recovery-deepseek-qwen-2026-11-06` | **Already superseded / no copy** | Current `main` already recognizes DeepSeek and Qwen routes and provider hosts. Current `browser_extension/content.js` is newer (676 lines vs 493 in the legacy branch), and current capture API tests cover five providers. The legacy branch's content script must not overwrite the newer implementation. |
| `feat/telescope-metadata-only-2026-11-03` | **Already integrated / no copy** | Current `main` contains `core/recovery/ai_source_inventory.py`, metadata-only `TelescopeAdapter`, the recovery API endpoint, inventory script and tests. The current adapter uses an explicit allowlist and avoids raw session detail payloads. |
| `feat/external-agent-readiness-probe-2026-11-03` | **Already integrated and evolved / no copy** | Current `main` contains `core/development/external_agent_probe.py` and the associated readiness API/security route. Current implementation includes additional safe-process handling and uses the existing local coding-agent probe for Codex. Replacing it with the older branch version would regress it. |
| `feat/browser-mission-queue-v1` | **Superseded / no copy** | The browser operator API and durable queue now exist in `main`. The extension installer PowerShell script in the legacy branch has the same blob SHA as current `main`; its install guide is not needed to recover implementation. |

## Preserved free-tier consultation files

- `core/recovery/browser_consult_store.py`
- `core/api/browser_consult_api.py`
- `tests/test_browser_consult_store.py`

The store is SQLite-backed and has explicit enablement and provider allowlisting, bounded prompts/responses, secret-pattern checks, cooldowns, idempotency, no automatic replay after ambiguous restart, and marks provider output as untrusted. The API uses the existing local audit writer.

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

The four legacy branches assessed as superseded/integrated may be considered for deletion only after the owner reviews this report and confirms that the source branches are no longer needed for provenance. Keep `feat/free-tier-browser-ai-consult-2026-11-05` until its isolated recovery PR is either completed or explicitly rejected. Preserve GitHub PR/commit history even after deleting branch refs.
