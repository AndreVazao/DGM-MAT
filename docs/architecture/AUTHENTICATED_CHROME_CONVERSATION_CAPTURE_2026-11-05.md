# Authenticated Chrome conversation capture — implementation contract

**Status:** implementation required; not yet operational  
**Operator authorization:** 2026-11-05, DGM-MAT Fixing 21  
**Tracking issue:** https://github.com/AndreVazao/DGM-MAT/issues/208

## Objective

DGM-MAT must recover the actual content of the operator's ChatGPT, Gemini and Grok conversations, not merely browser-history metadata or conversation titles. Capture is performed one conversation at a time through the provider's normal, visible, authenticated web interface and stored in the local recovery archive for later classification, project association and script recovery.

## Current truth — do not overstate capability

The current repository already contains:
- Chrome history/source metadata inventory in `core/recovery/ai_source_inventory.py`;
- an append-only SQLite recovery ledger in `core/recovery/recovery_ledger.py`;
- a safe ChatGPT export ZIP/JSON importer in `core/recovery/chatgpt_export_importer.py`;
- local import inbox routes in `core/api/recovery_api.py`;
- conversation intelligence records, message roles, user intents, AI proposals, decisions and relationships in `core/conversation_intelligence/models.py`;
- a governed Playwright session in `core/providers/browser/governed_browser_session.py`.

The existing GovernedBrowserSession still launches an isolated unauthenticated context. This branch now adds AuthenticatedChromeSession, a loopback-only Playwright CDP attachment primitive that reads visible page text and requires explicit tab selection when multiple provider tabs exist. It never reads browser storage or closes the user's Chrome process. The Chrome source inventory still reads metadata only; provider-specific conversation enumeration/capture adapters, archive ingestion wiring and live local acceptance are not yet implemented. Therefore end-to-end conversation recovery is **not yet operational or proven**.

## Approved browser boundary

Allowed:
1. Attach to an explicit local Chrome DevTools Protocol endpoint started by the operator/DGM-MAT, or launch a separately configured DGM-MAT-managed Chrome profile whose sign-in was completed by the operator.
2. Read only visible/rendered content and accessible DOM on explicit allowlisted origins:
   - ChatGPT: `chatgpt.com`, `chat.openai.com`
   - Gemini: `gemini.google.com`
   - Grok: `grok.com`, `x.com` only where the conversation UI itself is hosted there.
3. Navigate conversation lists and open each conversation in sequence, with bounded scrolling/pagination and deterministic checkpoints.
4. Capture the message text/role/order/timestamp and visible attachment references. Preserve variants/branches where the UI exposes them.
5. Stop cleanly on sign-in, MFA, CAPTCHA, rate-limit, provider warning, inaccessible content, unexpected DOM or navigation outside the allowlist.

Forbidden:
- Reading, exporting or logging cookies, localStorage, sessionStorage, IndexedDB, browser profile databases, passwords, API keys, bearer tokens or authentication state.
- Hidden/private API calls, endpoint reverse engineering, direct provider database access, or bypassing provider UI.
- CAPTCHA/MFA/paywall/rate-limit bypass.
- Sending prompts/messages, editing, deleting, liking, sharing or changing account settings.
- Capturing unrelated tabs, other accounts or non-provider pages.
- Sending conversation text/titles to GitHub, external LLMs or telemetry by default.

A CDP endpoint grants control of the visible browser and must be treated as a powerful local capability. Bind to loopback only, require explicit configuration, validate the exact browser target/origin before capture, and never expose the debugging port to the network.


## Chrome version and default-profile constraint

Chrome 136 and later no longer honor remote-debugging-port/pipe switches against the default Chrome data directory. A separate non-standard user-data directory is required for the classic CDP port workflow. Playwright also warns that automating the regular default Chrome profile is unsupported and recommends a separate profile. Therefore the CDP primitive in this branch is a supported path only when Chrome has an explicitly enabled loopback debugging endpoint; it must not be represented as a way to silently attach to the user's ordinary Chrome profile.

For the operator's existing authenticated default Chrome profile, evaluate these routes in order:
1. Chrome DevTools MCP auto-connect on Chrome 144+ after the operator explicitly enables Remote Debugging in chrome://inspect/#remote-debugging and approves Chrome's connection prompt. The approval is a deliberate browser security control; never attempt to suppress it.
2. A narrowly permissioned DGM-MAT Chrome extension using normal content scripts on the three provider origins, with a one-time operator pairing to the local DGM-MAT API. It must not request cookies, webRequest, browsing-history, storage or broad all-sites permissions.
3. A dedicated DGM-MAT Chrome profile with the operator signing in manually, then a loopback CDP endpoint. Do not copy the regular Chrome profile or its authentication data.

The implementation must detect which route is available and report the exact blocker rather than trying to read profile files or bypass Chrome's security boundary.

Official references:
- Chrome 136 remote-debugging change: https://developer.chrome.com/blog/remote-debugging-port
- Chrome DevTools MCP auto-connect and approval: https://developer.chrome.com/blog/chrome-devtools-mcp-debug-your-browser-session
- Playwright CDP attachment and default-profile warning: https://playwright.dev/python/docs/api/class-browsertype

## Capture pipeline

1. **Discover:** use existing local metadata inventory to find provider origins and conversation route IDs. Do not treat history as proof that a conversation still exists.
2. **Attach:** connect only to the explicitly configured local browser endpoint. Confirm the active page belongs to one of the allowlisted provider origins.
3. **Enumerate:** collect visible conversation links/IDs using provider-specific UI adapters. Use bounded list scrolling/pagination; save the discovered set and count.
4. **Capture one:** open one conversation, wait for stable UI, read visible message containers and role labels, capture all accessible messages, and determine whether the page indicates truncation/continuation/branching.
5. **Archive:** write immutable raw UI capture JSON and normalized JSON/Markdown under the local archive root. Keep source URL, provider, conversation ID, title, account label (operator-configured non-secret label), captured-at time, adapter version, ordered roles, timestamps, attachment references, completeness and SHA-256.
6. **Checkpoint:** register/update the existing RecoveryLedger. Mark only integrity-verified captures as captured; use partial/blocked_login/rate_limited/needs_user/failed for other outcomes. A crash must resume at the next incomplete conversation.
7. **Index:** pass normalized messages to the existing Conversation Intelligence pipeline. Preserve user requests separately from AI responses, suggestions, accepted decisions and superseded requirements.
8. **Classify:** suggest project/repository, owner, purpose, technologies, decisions, code artifacts, dependencies and follow-up tasks with evidence references and confidence. Unknown/ambiguous attribution remains unknown; do not silently assign.
9. **Report:** private local report includes per-provider counts, conversation IDs/titles, completeness, hashes, project classification and blockers. GitHub receives only redacted aggregate progress and test evidence.

## Provider adapter contract

Each adapter must implement the same small interface:
- `can_handle(url, page_title)`
- `enumerate_visible_conversations(page, max_pages, max_items)`
- `open_conversation(page, source_id)`
- `capture_visible_messages(page)`
- `detect_incomplete_or_blocked_state(page)`

Adapters must use semantic/accessibility selectors first and maintain fixture snapshots for selector regression tests. Do not rely on brittle positional selectors alone. The adapter must never click send, edit, delete or account-management controls.

Initial provider sequence: ChatGPT, then Gemini, then Grok. A provider can be marked blocked without preventing other providers from progressing.

## Data and idempotency

Reuse the current RecoveryLedger and archive/import pipeline. Do not create a second unrelated database. Use stable key `(provider, source_id)`; content hash determines whether a capture is unchanged or a new version. Keep old capture versions immutable when provider content changes. Capture and index states must be separate.

Recommended local layout:
```
DGM-MAT-Data/
  conversations/
    raw-ui/<provider>/<source_id>/<capture_id>.json
    normalized/<provider>/<source_id>/<capture_id>.json
    markdown/<provider>/<source_id>/<capture_id>.md
    manifests/<provider>/<source_id>/<capture_id>.manifest.json
  reports/
    conversation-recovery-progress.json
    conversation-recovery-progress.md
```

No private conversation content, account names or titles belong in the public repository.

## Verification gates

Unit/fixture tests:
- provider origin allowlist and redirect rejection;
- attach failure and missing endpoint;
- conversation enumeration across multiple pages/scrolls;
- stable ordering and duplicate suppression;
- user/assistant/tool role preservation;
- branch/variant retention where exposed;
- partial/truncated capture detection;
- blocked login/MFA/CAPTCHA/rate-limit states;
- attachment references without claiming attachment bytes were captured;
- deterministic IDs, content hashes and immutable versioning;
- interrupted run resumes without skipping or duplicating;
- archive write failure leaves ledger unclaimed/retryable;
- logs redact secrets and do not contain transcript bodies.

Local acceptance (required before declaring provider support complete):
- operator starts/authorizes the local browser endpoint;
- capture at least one real accessible conversation from that provider;
- compare message count/order against the rendered UI;
- verify archive hashes and local search/index;
- verify no account changes and no credential-store reads.

## Completion definition

The feature is complete only when all three provider adapters pass fixtures and local acceptance, the importer is connected to the real mission/checkpoint pipeline, local archive/search/classification works, and a restart resumes safely. A code merge or passing mock test alone is not proof of live account capture.
