# DGM-MAT Chrome conversation recovery extension

**Status:** implementation branch; local installation and live provider acceptance still required.

## Purpose

This Manifest V3 extension lets DGM-MAT read conversations that the operator can already see in authenticated ChatGPT, Gemini and Grok tabs. It discovers visible conversation links in the provider's rendered navigation, queues them locally, opens them one by one in the same tab, reads visible message containers and sends the capture to the loopback DGM-MAT API.

It does not call provider APIs, inspect browser authentication stores, or send prompts/messages.

## Permission boundary

The manifest requests only:
- `activeTab`: use the tab when the operator opens the extension popup;
- `storage`: persist the DGM-MAT local session token and recovery checkpoint in extension-owned storage;
- host access to ChatGPT, Gemini (including legacy `bard.google.com`), Grok and `http://127.0.0.1:8181` / `http://localhost:8181`.

It does not request `cookies`, `history`, `webRequest`, `debugger`, `downloads`, `scripting`, or broad all-sites access. The extension does not read `document.cookie`, localStorage, sessionStorage, IndexedDB or browser profile files.

The bearer token stored by the extension is a dedicated DGM-MAT `browser-capture` session, not a provider login token and not a general operator token. It can call only the browser-capture API routes. It is obtained by exchanging a one-time pairing code that expires after five minutes. The extension session expires after eight hours; ordinary mobile/local sessions retain their existing 30-minute lifetime. Restarting the DGM-MAT API invalidates in-memory sessions, so pair again after an API restart. Keep the provider tabs open while an unattended run is active.

## One-time installation and pairing

1. On the DGM-MAT PC, open Chrome and navigate to `chrome://extensions`.
2. Enable Developer mode, select **Load unpacked**, and choose this `browser_extension` directory.
3. Copy the extension ID displayed by Chrome. It must be a 32-character Chrome extension ID.
4. Configure the Windows environment variable `DGM_CHROME_EXTENSION_ID` to that exact ID for the DGM-MAT API process. Do not use a wildcard. Restart the DGM-MAT API after changing it.
5. On the same PC, open `http://127.0.0.1:8181/auth/pairing-code`. The page issues a one-use code with a five-minute expiry.
6. Open the DGM-MAT extension popup, enter that code and choose **Pair with DGM-MAT**. The code is consumed once; it is not saved.
7. Open the ChatGPT, Gemini or Grok conversation list while signed in normally. Open the extension popup and choose **Scan and recover this provider**. To let DGM-MAT continue unattended across already-open provider tabs, enable **Enable unattended recovery across open provider tabs** once. The extension remembers the provider tabs as their pages load and rotates through them sequentially; no per-conversation approval is required. The setting is off by default and can be disabled at any time. Reload provider tabs that were already open before the extension was installed so their content scripts register them.

Pairing must happen from the local PC. The API accepts only the exact configured extension origin and loopback network requests. Never expose port 8181 or the Chrome debugging port to the LAN or internet.

## Sequential workflow

- The extension scans the current provider's visible conversation links, including bounded scrolling of visible navigation areas (maximum 500 discovered links).
- DGM-MAT registers each source in the existing SQLite RecoveryLedger.
- The API claims one pending conversation. The extension navigates the same tab to that conversation.
- After the provider page renders, the extension reads provider-specific visible message containers. It scrolls the conversation container in bounded steps to collect content exposed by the rendered UI.
- The local API writes an immutable raw JSON capture, computes SHA-256 and verifies the archive, then creates a second redacted normalized copy and feeds that copy to the existing ConversationIntelligencePipeline.
- The extension requests the next source and repeats until the queue is empty. When unattended mode is enabled, it then continues to another already-open provider tab; blocked conversations remain queued for deliberate retry.
- Login, challenge, rate-limit, selector failure, unexpected navigation or archive failure stops the run and checkpoints the blocker. The operator can explicitly retry the blocked conversation from the popup after resolving the cause.

## Archive and truth labels

Raw captures are stored under the configured `DGM_RECOVERY_ARCHIVE_ROOT` (default: `~/.dgm-mat/recovery-archive/browser-ui/<provider>/...`). They contain the visible source content and should be treated as private local data. The normalized copy is redacted before indexing. GitHub receives no conversation bodies or titles.

A successful SHA-256 check proves that the local capture file was written intact. It does **not** prove that the provider rendered every historical turn. The current adapter reports `visible_snapshot` and `full_history_verified=false`; it never upgrades a visible snapshot into a claim of complete history.

## Current provider selector limits

- ChatGPT: `data-message-author-role` message containers.
- Gemini: `user-query` and `model-response` elements.
- Grok: visible conversation/message test IDs and message metadata; role inference may remain `unknown` where the UI does not expose speaker semantics.

Provider UIs change. Unknown layouts are reported as failures rather than silently archiving the whole page or inventing speaker roles. Attachment bytes are not downloaded; only text visible in message containers is captured.

## Local acceptance checklist

- [ ] Install unpacked extension and configure its exact ID in the DGM-MAT API environment.
- [ ] Pair with a one-time code and confirm the extension receives only the browser-capture scope and expires after eight hours.
- [ ] Enable unattended recovery and verify the extension rotates across already-open provider tabs without per-conversation prompts.
- [ ] Capture one conversation from ChatGPT, Gemini and Grok where accessible.
- [ ] Compare visible UI message order/count against the raw local archive.
- [ ] Verify SHA-256 and that the normalized archive redacts test secrets.
- [ ] Verify the conversation intelligence progress/knowledge stores contain the derived audit and code artifacts.
- [ ] Verify the extension stops on login/challenge/rate-limit and can explicitly retry.
- [ ] Confirm source conversations remain unchanged and no provider message was sent.

Do not mark the feature production-ready until all three real-provider acceptance checks pass on the operator's PC.


## Fresh EGM review context protocol (experimental, not wired to the queue)

The content script exposes two additional extension-only messages:

- `DGM_FRESH_REVIEW_PING`: checks that the current provider tab is on an allowlisted provider origin, is not blocked, has no recognized conversation ID, exposes a visible composer and has no visible user/assistant messages. It returns a one-shot preflight nonce.
- `DGM_EXECUTE_FRESH_REVIEW`: requires the exact nonce and unchanged tab URL/provider, rechecks the blank-page conditions, sends only the supplied bounded review prompt through the visible composer, and waits for a newly assigned conversation ID plus a stable assistant response.

The response deliberately reports `independence_attested=false`. It is UI-observed evidence that a blank page became a new conversation, not cryptographic proof that the provider has no hidden account-side context. The message handlers are not yet connected to the durable consultation queue or EGM task coordinator. This PR is intentionally stacked on the browser-recovery branch so its extension validation runs against the exact combined base. The current browser-consultation path continues to operate on existing conversations and must not be used as an EGM independent reviewer.

The preflight is one-shot and bound to the same tab URL. It now also requires provider-specific temporary privacy mode: ChatGPT Temporary Chat must be explicitly Unpersonalized, and Gemini Temporary Chat must be visibly active. Grok is not accepted yet because Private Chat alone does not verify its separate X-personalization setting is off; DeepSeek and Qwen are not accepted because this adapter has no verified temporary-mode contract for them. Existing conversation IDs, visible prior messages, missing composer, blocked provider, stale nonce, URL/provider changes, or failure to observe a new conversation ID all fail closed. Provider DOM behavior still requires live Windows/Chrome acceptance; deterministic fixtures do not replace it.


### Privacy-mode evidence basis checked 2026-11-08

- ChatGPT: OpenAI documents that an **Unpersonalized Temporary Chat** does not use Memory, custom instructions or plugins. Safety-relevant context may still be used in rare high-risk cases. See https://help.openai.com/en/articles/8914046-temporary-chat-in-chatgpt
- Gemini: Google documents Temporary Chat as not appearing in recent chats/Activity and not being used to personalize Gemini or train its models. See https://blog.google/products-and-platforms/products/gemini/temporary-chats-privacy-controls/ and https://gemini.google/release-notes/
- Grok: xAI documents Private Chat as hidden from history and deleted from its systems within 30 days, and separately exposes the “Personalize Grok using X” control. The current adapter cannot verify that the separate personalization control is disabled in the active browser context, so Grok remains blocked. See https://x.ai/legal/faq
- DeepSeek: its current privacy policy documents collection of prompts and chat history but does not define a temporary/isolated chat mode. See https://cdn.deepseek.com/policies/en-US/deepseek-privacy-policy.html
- Qwen: the available stateless API documentation is not evidence about the consumer browser UI. No official browser temporary-mode control has been verified in this implementation, so Qwen remains blocked.

These are provider product controls, not cryptographic isolation. The adapter therefore continues to report `independence_attested=false` until a trusted host workflow validates and records the evidence. Provider UI labels can change; missing or ambiguous labels must fail closed.


## EGM fresh-review queue bridge (experimental)

The extension can now consume an explicitly approved consultation marked `review_mode: "fresh_review"`. This is separate from the existing conversation-recovery mode.

1. The authenticated local DGM-MAT API queues one consultation per selected provider in the existing SQLite browser-consultation store. Fresh mode currently accepts only ChatGPT and Gemini.
2. Every consultation remains `PENDING_APPROVAL`; each provider request must be approved individually in the existing popup.
3. The extension peeks at the next approved queue item without claiming it, then checks only the matching readiness mode. For fresh mode it requires the provider's explicit active privacy controls, a blank page, no recognized conversation ID, no visible prior messages and a visible composer. A failed preflight leaves the approved item pending; it does not consume a claim or trigger a cooldown.
4. Before sending, the content script repeats the checks and consumes a one-shot nonce bound to the exact provider tab URL. It then waits for a new conversation ID and a stable response.
5. The result API requires the host-observed privacy-mode and new-conversation evidence. Evidence and response are persisted with the consultation; a restart never replays a claimed consultation.
6. The authenticated endpoint `GET /recovery/browser-consult/fresh-review/{review_id}` resumes the durable review and returns each provider's status, response and evidence.

The read-only `GET /recovery/browser-consult/peek?provider={provider}` endpoint lets the extension choose the correct preflight before consuming the one-shot claim. Enqueue uses the existing `POST /recovery/browser-consult/enqueue` contract with `review_mode: "fresh_review"` and a unique `review_id`; it still requires `free_capacity_confirmed: true`, explicit individual approval and the existing opt-in flag. Do not enable the flags merely to test the code.

**Important:** this bridge records provider UI evidence, not a trusted runtime isolation attestation. The stored result remains untrusted and `independence_attested=false`; it cannot yet be passed as a successful `RuntimeIsolationAttestation` to `DesignReviewCoordinator`. A later host-side verifier must reconcile the durable result with the EGM task/mission, verify reviewer mapping and policy, then persist the final task receipt through the existing OrganizationTaskManager. No synchronous worker waits for operator approval.
