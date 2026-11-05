# DGM-MAT Chrome conversation recovery extension

**Status:** implementation branch; local installation and live provider acceptance still required.

## Purpose

This Manifest V3 extension lets DGM-MAT read conversations that the operator can already see in authenticated ChatGPT, Gemini and Grok tabs. It discovers visible conversation links in the provider's rendered navigation, queues them locally, opens them one by one in the same tab, reads visible message containers and sends the capture to the loopback DGM-MAT API.

It does not call provider APIs, inspect browser authentication stores, or send prompts/messages.

## Permission boundary

The manifest requests only:
- `activeTab`: use the tab when the operator opens the extension popup;
- `storage`: persist the DGM-MAT local session token and recovery checkpoint in extension-owned storage;
- host access to the three provider sites and `http://127.0.0.1:8181` / `http://localhost:8181`.

It does not request `cookies`, `history`, `webRequest`, `debugger`, `downloads`, `scripting`, or broad all-sites access. The extension does not read `document.cookie`, localStorage, sessionStorage, IndexedDB or browser profile files.

The bearer token stored by the extension is a short-lived DGM-MAT local operator session, not a provider login token. It is obtained by exchanging a one-time pairing code that expires after five minutes. The local session expires after 30 minutes.

## One-time installation and pairing

1. On the DGM-MAT PC, open Chrome and navigate to `chrome://extensions`.
2. Enable Developer mode, select **Load unpacked**, and choose this `browser_extension` directory.
3. Copy the extension ID displayed by Chrome. It must be a 32-character Chrome extension ID.
4. Configure the Windows environment variable `DGM_CHROME_EXTENSION_ID` to that exact ID for the DGM-MAT API process. Do not use a wildcard. Restart the DGM-MAT API after changing it.
5. On the same PC, open `http://127.0.0.1:8181/auth/pairing-code`. The page issues a one-use code with a five-minute expiry.
6. Open the DGM-MAT extension popup, enter that code and choose **Pair with DGM-MAT**. The code is consumed once; it is not saved.
7. Open the ChatGPT, Gemini or Grok conversation list while signed in normally. Open the extension popup and choose **Scan and recover this provider**.

Pairing must happen from the local PC. The API accepts only the exact configured extension origin and loopback network requests. Never expose port 8181 or the Chrome debugging port to the LAN or internet.

## Sequential workflow

- The extension scans the current provider's visible conversation links, including bounded scrolling of visible navigation areas (maximum 500 discovered links).
- DGM-MAT registers each source in the existing SQLite RecoveryLedger.
- The API claims one pending conversation. The extension navigates the same tab to that conversation.
- After the provider page renders, the extension reads provider-specific visible message containers. It scrolls the conversation container in bounded steps to collect content exposed by the rendered UI.
- The local API writes an immutable raw JSON capture, computes SHA-256 and verifies the archive, then creates a second redacted normalized copy and feeds that copy to the existing ConversationIntelligencePipeline.
- The extension requests the next source and repeats until the queue is empty.
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
- [ ] Pair with a one-time code and confirm the local session expires.
- [ ] Capture one conversation from ChatGPT, Gemini and Grok where accessible.
- [ ] Compare visible UI message order/count against the raw local archive.
- [ ] Verify SHA-256 and that the normalized archive redacts test secrets.
- [ ] Verify the conversation intelligence progress/knowledge stores contain the derived audit and code artifacts.
- [ ] Verify the extension stops on login/challenge/rate-limit and can explicitly retry.
- [ ] Confirm source conversations remain unchanged and no provider message was sent.

Do not mark the feature production-ready until all three real-provider acceptance checks pass on the operator's PC.
