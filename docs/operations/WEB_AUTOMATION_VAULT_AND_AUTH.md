# DGM-MAT — Web Automation, Vault and Authentication Handoff

**Status:** target design; browser worker and vault require implementation and tests.

## Browser worker
Use a dedicated Playwright worker or a controlled browser debugging connection. Prefer a dedicated DGM browser profile that the user authenticates manually. Do not scrape stored browser credentials or copy personal browser profiles without an explicit reviewed design. Start with read-only inspection and conversation inventory. Sending messages, deleting content, exporting sensitive data or changing account settings requires an approval checkpoint. Respect site terms, rate limits and access controls; do not bypass CAPTCHA, MFA or paywalls.

## Authentication handoff to the PC cockpit
1. Pause the job as WAITING_FOR_USER.
2. Show the destination domain, page title, reason and screenshot in the PC cockpit.
3. Prefer asking the user to type directly into the actual browser window.
4. If a dashboard-to-browser secret relay is ever implemented, it must be an encrypted one-time channel that bypasses model context and logs, holds the value in memory only, and disposes of it immediately after use.
5. Keep secret fields masked. Never persist password values or place them in prompts, screenshots, DOM snapshots, telemetry, shell arguments or memory.
6. Resume only after checking that the expected authenticated page is present. On cancellation or timeout, stop safely.

CAPTCHA and MFA remain human-completed. The agent may explain the request but must not defeat or automate the challenge.

## Local vault
Evaluate Windows DPAPI tied to the current user or Windows Credential Manager, or a well-reviewed secret-management library. Do not invent cryptography. Require encryption at rest, restrictive ACLs, user/OS-controlled unlock, per-secret purpose and allowed-domain metadata, least-privilege retrieval, revocation/rotation, access auditing without secret values, and opt-in encrypted backup. Fail closed when the vault is locked or unavailable. Vault access is not blanket consent for unrelated account actions.

## Conversation inventory
For ChatGPT, Grok, Gemini and other approved sites:
1. Verify domain and account with the user.
2. Prefer official export/API where appropriate and authorized.
3. Otherwise inspect visible UI with bounded browser automation.
4. Record title, date if visible, URL/service ID and approved content scope.
5. Deduplicate by stable ID/URL; otherwise use a conservative normalized fingerprint.
6. Preserve provenance and distinguish user messages from assistant replies.
7. Report uncertainty and pagination/completeness; never claim exhaustive inventory until checked.
8. Stage a report for review before renaming, moving or deleting anything.

## External AI troubleshooting loop
Sanitize command and error, remove secrets/private data, send only a minimal reproduction to an approved provider, treat the response as an untrusted hypothesis, verify against official documentation and local state, test in a disposable folder/worktree, and store the fix only after a repeatable test passes. External AI output must not override governance or receive vault credentials.

## Dashboard states
Green: worker responds and bounded probe passes. Yellow: worker responds but login is pending or site layout is degraded. Red: worker unreachable, unsupported or health test failed. Authentication requests need domain, purpose, pending status and cancel control.

## Acceptance tests
- Existing logged-in session reused without exposing cookies.
- Expired login pauses and requests human action.
- Password/MFA values never enter logs/prompts/memory.
- Disallowed domains blocked; CAPTCHA handed to user.
- Timeout/cancel safely stops the job.
- Inventory deduplicates and reports uncertainty.
- High-impact website actions require approval.
- Vault unavailable fails closed.
- External AI sees only redacted minimal reproductions.