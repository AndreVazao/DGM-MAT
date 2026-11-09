# EGM Browser Fresh-Review Durable Bridge

Date: 2026-11-09
Status: experimental implementation; no production activation

## Purpose

Connect the EGM fresh-review protocol to the existing free-tier browser consultation queue without creating a second queue or blocking a synchronous worker while an operator approves provider use.

## Lifecycle

1. The local authenticated API accepts a consultation with `review_mode=fresh_review`, a bounded `review_id`, a task reference, and exactly both ChatGPT and Gemini providers. A single provider is rejected.
2. The existing SQLite `browser_consultations` table stores `review_mode`, `review_id`, status, prompt digest, response digest, and serialized UI evidence. Existing rows migrate with `review_mode=standard`; the existing table and queue remain authoritative.
3. Each provider item starts in `PENDING_APPROVAL`. The operator approves each provider separately through the existing popup. Free-tier capacity attestation and the existing disabled-by-default opt-in remain mandatory.
4. The extension calls the read-only `GET /recovery/browser-consult/peek` before claiming. It then checks only the required UI mode. A missing privacy-mode preflight leaves the item pending and consumes no claim or cooldown.
5. `POST /recovery/browser-consult/next` atomically claims the approved item with the existing one-shot claim token. The extension persists the claim locally before interacting with the provider.
6. Fresh mode requires an explicit active/checked privacy UI state, a blank page, no recognized conversation ID, no visible prior messages, and a visible composer. The content script repeats checks and consumes a one-shot nonce bound to the provider and exact tab URL.
7. Completion requires a newly observed conversation ID, a stable assistant response, and evidence containing provider, privacy mode, empty initial source ID, zero visible initial messages, and verification method. Evidence is validated against the claimed provider and provider-specific privacy-mode contract before it is persisted.
8. The authenticated `GET /recovery/browser-consult/fresh-review/{review_id}` endpoint resumes the durable review. It returns expected providers, actual provider count, per-provider statuses, untrusted response text, evidence, and hashes. A missing or cooldown-blocked provider keeps the aggregate review pending/incomplete. Interrupted claims are marked blocked on restart and are never replayed.

## Security boundaries

- Only ChatGPT Temporary Chat + Unpersonalized and Gemini Temporary Chat are currently accepted. Grok, DeepSeek, and Qwen fail closed.
- Labels alone are insufficient: the extension requires explicit active/checked UI state. If the UI does not expose a verifiable active state, the provider is not ready.
- The operator must approve each provider consultation individually.
- The extension never receives general operator scope. Peek and result-resume routes are classified under the narrow browser-capture scope.
- Prompts and responses remain bounded; existing redaction and secret-response blocking continue to apply.
- The queue does not auto-retry, auto-approve, invoke paid APIs, read cookies/passwords, or bypass provider UI.
- Existing standard consultation mode remains unchanged.

## EGM integration boundary

The durable bridge records provider UI observations; it does **not** create a `RuntimeIsolationAttestation`. It deliberately returns `independence_attested=false` and `result_trusted=false`.

A later host-side verifier must:
- bind the review ID and task reference to an existing RUNNING EGM task and mission;
- verify the expected reviewer/provider mapping and that every required reviewer completed;
- inspect the persisted evidence and reject missing, duplicate, stale, or mismatched contexts;
- create a trusted host attestation only if the host can prove the complete isolation policy;
- convert results into the existing typed `ReviewerResult` contract; and
- persist the final receipt through `OrganizationTaskManager.complete_with_result`.

Until that verifier exists, browser results must not be passed to `DesignReviewCoordinator` as successful independent reviews. The current implementation is an asynchronous evidence-intake and resume layer only.

## Validation gates

- Deterministic fixtures for ChatGPT/Gemini privacy-mode controls and fail-closed unsupported providers.
- Store tests for migration, per-provider approval, one-shot claim, evidence validation, durable resume, and non-mutating peek.
- API tests for narrow route classification, supported-provider enforcement, approval, claim, result persistence, and resume.
- Chrome extension validation, Bandit, pip-audit, and Windows executable build.
- Live Windows 10 + Chrome acceptance with the actual ChatGPT/Gemini UI is still required. CI fixtures do not prove live provider DOM compatibility.

## Activation

Keep all browser consultation and AutoHelp flags disabled. Do not merge or enable the protocol based solely on CI. No real provider account was accessed during implementation.
