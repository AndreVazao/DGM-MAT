# DGM-MAT automatic help — free-only policy

The automatic help worker is disabled by default. It only consults external agents when a local actionable request has no registered executor; it does not delegate execution or grant repository write access.

## Existing free providers

Kilo and LLM7 remain the default allowlist. Codex and Claude Code are opt-in external agents and are never selected merely because they are installed.

## Explicit local opt-in

To enable Codex and Claude Code on an operator-controlled installation, configure all of the following:

- `DGM_AUTONOMY_HELP_ENABLED=1`
- `DGM_AUTONOMY_HELP_EXTERNAL_AGENTS_ENABLED=1`
- `DGM_AUTONOMY_HELP_FREE_CAPACITY_CONFIRMED=1`
- `DGM_AUTONOMY_HELP_PROVIDERS=codex,claude`

The capacity flag is an operator attestation, not a numeric quota reading. DGM-HUB does not expose remaining free quota. Stop on an explicit rate, quota, or capacity error; never fall back to a paid route.

## Runtime gates

- Codex and Claude must be enabled and ready in DGM-HUB.
- Their latest provider status must include `response_verified=true`; after a Hub restart, run a fresh evidence-backed probe before automatic use.
- The bounded consultation wait is 180 seconds. DGM-HUB's Claude execution limit is 150 seconds.
- No automatic retry is performed after an ambiguous request or provider failure.
- External answers are persisted as untrusted suggestions. They require independent review and are never promoted directly into trusted project memory.
- No source files, credentials, tokens, or conversation history are sent by this worker. Only the blocked goal and capability boundary are shared.

This worker currently handles unsupported actionable requests received through the mobile runtime. It is not a general autonomous coding scheduler for every desktop mission.

## Evidence contract

Every factual claim sent back by Codex or Claude must cite an exact `[E#]` identifier from the DGM-HUB `CONTEXTO DE EVIDÊNCIA` block. The agents must not invent references or cite `CONTEXTO AUTORIZADO`. When the Hub withholds a response for missing citations, DGM-MAT records `BLOCKED_EVIDENCE`, keeps the original provider response in Hub history, and does not promote it into trusted local knowledge.
