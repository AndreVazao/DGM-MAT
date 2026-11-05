# Authenticated Chrome conversation recovery — implementation contract

**Status:** first end-to-end implementation in PR #210; live provider acceptance still required  
**Operator authorization:** 2026-11-05, DGM-MAT Fixing 21  
**Tracking:** [issue #208](https://github.com/AndreVazao/DGM-MAT/issues/208)  
**Implementation:** [PR #210](https://github.com/AndreVazao/DGM-MAT/pull/210)

## Objective

DGM-MAT must recover the actual content of the operator's ChatGPT, Gemini and Grok conversations, not merely browser-history metadata or conversation titles. Capture runs through a least-privilege Chrome extension using the provider's normal rendered, authenticated UI. The extension discovers conversation links and captures one conversation at a time into the existing local RecoveryLedger and recovery archive.

The extension also supports an explicit unattended mode. After one-time pairing and enablement, it can rotate through already-open provider tabs without asking for approval for every conversation. Auto mode is off by default.

## Current implementation

The repository contains:
- Chrome history/source metadata inventory in `core/recovery/ai_source_inventory.py`;
- the shared append-only SQLite RecoveryLedger in `core/recovery/recovery_ledger.py`;
- ChatGPT export ZIP/JSON importer in `core/recovery/chatgpt_export_importer.py`;
- local import inbox and shared ledger in `core/api/recovery_api.py`;
- conversation-intelligence models and stores in `core/conversation_intelligence/`;
- local capture endpoints in `core/api/browser_capture_api.py`;
- a Manifest V3 extension in `browser_extension/`.

The extension:
1. pairs using the existing one-time local pairing-code flow;
2. receives a dedicated eight-hour `browser-capture` session, not a general operator token;
3. requests only `activeTab` and `storage` permissions plus explicit provider and loopback API host access;
4. discovers visible conversation links with bounded navigation scrolling;
5. claims sources from the shared RecoveryLedger, scoped to the selected provider;
6. opens and captures each conversation in sequence;
7. writes immutable raw captures with content fingerprints and SHA-256 verification;
8. creates a redacted normalized copy and feeds the existing ConversationIntelligencePipeline and ConversationKnowledgeStore;
9. checkpoints blocked/login/challenge/rate-limit/failure states and requires deliberate retry.

Automated tests cover API security, origin pairing, extension scope isolation, archive integrity, deduplication, provider queue isolation and ledger resume behavior. The extension workflow also validates JavaScript syntax and packages a ZIP artifact.

**Do not claim live recovery is complete yet.** No real authenticated provider account has been tested in this environment. Provider selectors may change, and local acceptance on the operator's PC is still required.

## Approved browser boundary

Allowed:
- Read only visible/rendered content and accessible DOM on:
  - ChatGPT: `chatgpt.com`, `chat.openai.com`
  - Gemini: `gemini.google.com`, legacy `bard.google.com`
  - Grok: `grok.com`, and `x.com/i/grok` only where the Grok UI is hosted there.
- Use bounded navigation scrolling and bounded conversation scrolling.
- Capture message text, role, order, visible timestamps and message IDs when exposed by the DOM.
- Keep a provider tab open and allow the extension to navigate it during an explicitly started/auto-enabled run.
- Stop on login, MFA, CAPTCHA, rate-limit, provider warning, inaccessible content, unexpected DOM or navigation outside the allowlist.

Forbidden during historical recovery:
- Reading, exporting or logging cookies, localStorage, sessionStorage, IndexedDB, browser profile databases, passwords, API keys, provider bearer tokens or authentication state.
- Hidden/private API calls, endpoint reverse engineering, direct provider database access or provider API scraping.
- CAPTCHA/MFA/paywall/rate-limit bypass.
- Sending prompts/messages, editing, deleting, liking, sharing or changing account settings.
- Capturing unrelated tabs or non-provider pages.
- Sending transcript bodies/titles to GitHub, external LLMs or telemetry by default.

The extension's local bearer token is a DGM-MAT session, not a provider login token. It has only the `browser-capture` scope and cannot access general operator routes. The extension origin must be configured by exact ID in `DGM_CHROME_EXTENSION_ID`; wildcards are denied. The API remains loopback-only.

## Capture and archive semantics

1. **Discover:** read visible provider conversation links. Chrome history metadata is only a discovery hint, never proof that a conversation still exists.
2. **Queue:** register sources in the existing shared RecoveryLedger. The queue is provider-scoped; late discoveries are not skipped behind the progress cursor.
3. **Capture one:** open one conversation, wait for rendered messages, collect recognized visible message containers and scroll the conversation container in bounded steps.
4. **Raw archive:** store immutable JSON under `DGM_RECOVERY_ARCHIVE_ROOT/browser-ui/<provider>/<source-key>/`. The content fingerprint excludes capture time, so unchanged content is idempotent. New content produces a new immutable version. SHA-256 is computed and verified for the actual file.
5. **Normalized archive:** redact secrets in a separate normalized copy before indexing. Raw content remains local and private; GitHub receives no transcript bodies or private titles.
6. **Index:** pass the normalized record to ConversationIntelligencePipeline. User messages become unverified request candidates. Selected AI recommendations become unaccepted proposal candidates. Possible confirmation phrases create review tasks only. **No user decision is auto-confirmed.**
7. **Project attribution:** use pipeline suggestions when evidence supports them. Otherwise create a review task; do not invent a project, owner or repository.
8. **Progress:** report per-provider discovery counts, pending/captured/blocked states, message counts, hashes, index status and truncation. Do not report a complete history when only visible content was captured.

Successful SHA-256 verification proves local file integrity only. Every capture is labelled `visible_snapshot` and `full_history_verified=false`. A bounded navigation scan can also report `discovery_truncated=true`. A provider-specific selector failure is a blocker, not a reason to archive the whole page as if it were a conversation.

## Provider adapter behavior and limits

- ChatGPT: `[data-message-author-role]` message containers.
- Gemini/Bard: `user-query` and `model-response` elements.
- Grok: visible conversation/message test IDs and metadata; role inference may remain `unknown` when the UI exposes no speaker semantics.

The extension does not download attachment bytes. It captures text visible in message containers. Identical repeated messages without stable provider message IDs may be deduplicated by text fingerprint; this is a known selector limitation to validate locally.

## Unattended operation

- Auto mode is off by default.
- The operator installs the unpacked extension once, configures its exact ID in the DGM-MAT API environment, pairs once and enables unattended mode from the extension popup.
- The extension remembers provider tabs as their content scripts load and rotates through already-open ChatGPT, Gemini and Grok tabs. No per-conversation approval is required.
- Keep provider tabs open. Reload tabs that were open before extension installation.
- The extension session expires after eight hours. Restarting the DGM-MAT API invalidates in-memory sessions and requires re-pairing.
- A blocked conversation is not retried automatically. The operator must use the explicit retry control after resolving the cause.
- Disabling auto mode prevents future automatic starts; an active queue continues until it is stopped or finished.

## Free-tier AI consultation

Historical recovery remains read-only. Outbound AI consultation through free-tier web UIs is tracked separately in [issue #211](https://github.com/AndreVazao/DGM-MAT/issues/211). It must use a distinct workflow, default off, sanitized minimal prompts, local audit records, provider cooldowns and unaccepted proposal records. It must not send full archives or silently change provider accounts. No paid API or paid model upgrade is allowed.

## Verification gates

Automated:
- provider origin allowlist and Grok `x.com/i/grok` restriction;
- exact extension origin pairing and no wildcard;
- extension token can call only browser-capture routes;
- one-time pairing and eight-hour scoped session;
- discovery/claim/capture/block/retry API behavior;
- provider-scoped queue claims and late-discovery resume;
- duplicate suppression, immutable content versions and SHA-256 checks;
- redacted normalized JSON is valid and indexed;
- user requests and AI proposal candidates remain unconfirmed;
- JavaScript syntax, manifest permissions and package artifact.

Local acceptance required before production-ready:
- install the extension on the operator's PC;
- configure the exact extension ID and restart DGM-MAT API;
- pair and enable unattended mode;
- capture at least one real accessible conversation from ChatGPT, Gemini and Grok;
- compare visible UI message count/order against the raw archive;
- verify raw and normalized hashes, redaction and local intelligence records;
- verify blocked/login/rate-limit states stop safely and deliberate retry works;
- verify source conversations remain unchanged and no provider message was sent.

Completion requires all three provider local acceptance checks, restart/resume verification, searchable local archive and evidence-backed project classification. A passing mock test or merged PR alone is not proof of live account capture.
