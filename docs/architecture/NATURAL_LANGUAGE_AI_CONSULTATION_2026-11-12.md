# Natural-language AI consultation in the active DGM-MAT chat

**Date:** 2026-11-12  
**Repository:** `AndreVazao/DGM-MAT`  
**Related issue:** [#313](https://github.com/AndreVazao/DGM-MAT/issues/313)  
**Status:** implementation plan grounded in current `main`; no provider transport is being activated by this document.

## Operator outcome

The operator should be able to write naturally in the current chat:

- `Pede ajuda ao ChatGPT sobre este erro.`
- `Consulta o Grok e o Gemini e compara as respostas.`
- `Pergunta ao Claude e ao DeepSeek se esta arquitetura faz sentido.`

DGM-MAT should identify the explicitly named provider(s), use the active thread and relevant current mission context, send only a bounded/redacted prompt through a supported configured transport, and return each real response as a provider-attributed message in the same thread. The operator must not be sent to a separate modal or asked to fill technical mission/context fields.

The button **Pedir ajuda a uma IA** remains as a secondary manual route: a compact inline selector inside the chat, with multi-select, current provider readiness, an editable question, and a short context disclosure. It must not open a separate top-level dialog.

## Verified current implementation (main, inspected 2026-11-12)

1. `cockpit/widgets/command_console.py` opens `AIConsultationDialog` with `dialog.exec()`. This is a separate modal window. The chat command path persists the user message and submits every normal directive as a runtime mission; there is no provider-intent parser in this path.
2. `cockpit/workspace/ai_consultation_dialog.py` asks for a mission ID, a separate goal, a separate context, provider checkboxes, a free-capacity checkbox, a generated preview, and then a queue action. This is the high-friction flow reported by the operator.
3. The desktop dialog exposes only five providers: ChatGPT, Gemini, Grok, DeepSeek and Qwen. Claude is missing from its provider list.
4. `core/recovery/browser_consult_store.py` currently allowlists those same five providers. `core/api/browser_consult_api.py` uses a matching five-provider Literal on enqueue/peek/claim. Therefore Claude is **not** currently end-to-end supported by this consultation queue.
5. The browser content script recognizes Claude's hostname, but hostname recognition is not proof of a working, policy-compliant consultation adapter. Claude must not be advertised as available until the server queue, provider readiness, visible send/response capture, persistence and a real E2E test all support it.
6. The browser extension polls the consultation queue only when its local AI-consultation toggle is enabled, it is paired, and a registered provider tab is available. It currently processes one consultation at a time. Merely enqueueing a request does not send it.
7. Every consultation is created pending approval and is approved through a separate endpoint. The current desktop dialog performs those approvals itself after enqueue. A natural-language path therefore needs a deliberate, auditable authorization mapping; it cannot just call enqueue and claim the AI was consulted.
8. The browser transport uses visible provider pages, checks for a matching provider tab and existing conversation, verifies the user prompt was submitted, waits for a stable assistant response, and blocks on login/challenge/rate-limit/UI mismatch. These fail-closed checks must remain.
9. The result endpoint appends a completed external answer to the linked local thread as an **untrusted external suggestion**. The desktop chat does not currently subscribe to consultation completion or poll for newly appended provider messages, so the operator may not see the response immediately in the open transcript without a refresh/reopen.
10. The fresh-review path is a distinct mode with stronger blank-page/privacy-mode evidence and currently requires both ChatGPT and Gemini. It must not be conflated with ordinary consultation in an existing conversation.

## Target interaction contract

### A. Natural language is the primary path

- Recognize explicit Portuguese and English request forms, including singular and multiple providers.
- Provider names and aliases must map deterministically to canonical IDs. Do not guess a provider if none is named and no explicit user preference exists.
- The phrase explicitly requesting a provider consultation is the operator's consent to send that specific request and the minimum relevant context to those named providers. Do not ask for a redundant second confirmation for this ordinary, explicit action.
- Persist the user's original message first, then create one durable consultation per selected provider, linked to the current chat thread and source mission when one exists.
- Use the remainder of the user's message as the task. If the message only says `Pede ajuda ao ChatGPT`, use the current message/thread context; ask one short clarification only if there is no meaningful question or context.
- Show a small inline status in the same transcript: preparing, queued, waiting for provider tab, sent, answered, blocked or failed. A queued request is never described as sent; a sent prompt is never described as answered.
- Append each provider response to the active thread with provider identity, timestamp and provenance. Partial success must be visible if another selected provider fails.
- For a request with no named provider, ask which provider(s) to consult rather than silently choosing.

### B. Manual button is a secondary route

- Replace the modal dialog with an inline panel in the current chat.
- Show all six requested conversational providers. Each must show a truthful state: ready, not configured, unsupported, blocked or unknown.
- Multi-select is required. Do not disable a provider merely because it is not allowlisted without explaining why.
- Default the question to the current user request/selected chat context; avoid manual mission-ID entry.
- Put advanced context review behind a compact disclosure, not in the primary interaction.
- Local coding agents Codex Free and Claude Code Free remain a separate category of execution agents, not conversational providers.

### C. Consent, privacy and free-tier controls

- A clear natural-language request to consult named providers is sufficient user intent for that consultation; do not introduce a redundant confirmation dialog.
- The transport must still be locally enabled and explicitly configured for free-tier use. If it is disabled, not paired, lacks a provider tab, or cannot verify account/channel readiness, explain the exact blocker and do not pretend to send.
- No paid API fallback, hidden provider API, credential scraping, CAPTCHA/MFA bypass or automatic retry after an ambiguous send.
- Redact secrets and bound context before release. Do not send unrelated threads, private history, tokens, cookies, credentials or unrelated repository files.
- Keep visible UI checks and provider-specific privacy/readiness gates. If a provider requires a temporary/isolated mode that cannot be verified, block that provider rather than weakening the check.
- Store prompt/response digests, provider, transport, source thread/mission, timestamps, state and evidence. External responses remain untrusted proposals; no code changes, approvals, merges or deployments follow automatically.

## Recommended implementation slices

### Slice 1 — Chat intent and transcript plumbing
- Add a deterministic, unit-tested provider-intent parser for the six canonical provider names and common Portuguese/English forms.
- Add explicit dispatch classification before normal mission submission, without breaking ordinary mission commands.
- Build a bounded context package from the current thread and active mission; use the existing redaction pipeline and persist a context digest.
- Add a durable consultation/thread correlation ID and a way for the desktop chat to observe result completion without restarting the chat.

### Slice 2 — Server orchestration
- Add an authenticated operator endpoint for a natural-language consultation request.
- Accept only explicit provider IDs, thread ID, bounded goal/context, and a server-verified configured free-provider set.
- Treat the explicit chat intent as the operator authorization for the named provider(s); record that authorization in the audit trail.
- Enqueue and release each approved request through the existing one-shot claim flow, without granting the browser extension general operator scope.
- Return durable per-provider IDs and truthful states. Multi-provider dispatch is partial-success aware and idempotent.

### Slice 3 — Provider capability matrix
- Keep ChatGPT, Grok, Gemini, DeepSeek and Qwen as separate capability entries; readiness is based on actual transport, not a hardcoded checkbox.
- Bring Claude into the server/store/extension queue only after implementing and testing its visible UI send, stable response capture, blocking behavior and result persistence.
- Never label all six as ready just because six names are displayed.

### Slice 4 — Inline manual selector
- Replace `AIConsultationDialog.exec()` with an inline chat panel.
- Add accessible multi-select chips/checkboxes, provider readiness text, a prefilled editable question and concise context disclosure.
- Keep advanced prompt inspection available without making it a multi-screen workflow.

### Slice 5 — End-to-end acceptance
For each provider independently, and for multi-provider combinations:
1. Explicit natural-language request in an existing desktop chat.
2. Correct provider parse and thread correlation.
3. Local enablement, paired extension and provider-tab readiness verified.
4. Actual visible UI prompt submission observed.
5. Stable assistant response observed.
6. Response stored and rendered in the same active desktop thread.
7. Provider failure/partial success reported accurately.
8. Restart and ambiguous interruption do not replay a consultation.
9. No paid fallback and no automatic code modification.

## Non-goals / prohibited shortcuts

- Do not reintroduce the legacy direct-send extension path.
- Do not bypass the current browser operator queue or its one-shot claim token.
- Do not turn a pending queue item into a success message.
- Do not mark Claude ready before full server-to-browser E2E validation.
- Do not remove privacy-mode/readiness checks merely to make the UI appear functional.
- Do not merge or install this work based only on a green syntax check; run focused tests, extension validation, Windows build and real Windows/Chrome acceptance.

## Current delivery status

- GitHub code and tests inspected; the findings above are grounded in the current `main` source.
- The operator's interaction requirements are recorded in issue #313.
- This document is a design/implementation checkpoint only. No runtime flags, extension toggles, provider accounts, PC files or local services were changed.
- Natural-language consultation, inline selector and real provider E2E are **not yet implemented**.
