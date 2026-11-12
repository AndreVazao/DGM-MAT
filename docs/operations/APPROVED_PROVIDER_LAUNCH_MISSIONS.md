# Approved AI provider launch from missions

## Scope

A mission with an explicit request such as `abre o chatgpt` or `open Gemini`
is routed to a fixed provider home page. The provider URL is selected from a
hard-coded allowlist; arbitrary URLs and browser commands are not accepted.

The launch is a desktop side effect and therefore requires the normal
`SafeActionQueue` operator approval. No mission is auto-approved by this
feature.

## Execution contract

1. The intent router recognizes an explicit launch verb and one supported
   provider name.
2. `MissionEngine` confirms the provider is in the launcher's allowlist.
3. The mission is queued for operator approval.
4. After approval, `webbrowser.open` asks the operating system to open the
   fixed HTTPS provider home page in the default browser.
5. The mission result records `OPEN_REQUESTED`, `launch_accepted_by_os`,
   `page_load_verified=false`, and `message_sent=false`.

A successful OS launch request is not proof that the page finished loading,
that the user is authenticated, or that the browser extension is paired.
The mission must never describe this operation as a provider consultation.

## Provider consultation remains separate

Sending a prompt to ChatGPT or another provider continues to use the existing
Browser Consultation queue and paired Chrome extension. That path retains
redacted prompt preview, free-tier capacity attestation, explicit operator
approval, one-shot claim tokens, and durable response storage. This change
does not bypass those controls or enable the consultation feature flag.

## Security boundaries

- No cookies, passwords, browser databases, local storage, or session tokens
  are read or exported.
- No message is composed or sent by the provider launcher.
- No arbitrary URL, shell command, or executable path is accepted.
- Browser launch failure produces a failed mission, not a success result.
- Tests stub the operating-system browser call; live Windows/Chrome acceptance
  remains a required PC-side validation.
