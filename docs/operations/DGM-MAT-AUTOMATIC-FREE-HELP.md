# DGM-MAT automatic free-only help

**Status:** implemented behind the operator-controlled `DGM_AUTONOMY_HELP_ENABLED` switch.

## Behavior

When a user sends an actionable request for which the mission router has no registered executor, the mobile conversation service:
1. Keeps the request and intent decision in the durable conversation thread.
2. Does not create a fictitious mission or queue action.
3. Enqueues one durable consult request, deduplicated by normalized goal for 24 hours.
4. A background worker checks the local DGM-HUB provider readiness and asks only the configured free allowlist.
5. Stores returned answers as untrusted specialist results and requests independent internal review.
6. Appends the response to the same conversation thread when the consultation finishes.

Supported read-only missions continue through their registered handlers and do not trigger external consultation.

## Free-only provider policy

The default allowlist is:
- `kilo` — Kilo's legitimate free route.
- `llm7` — anonymous/no-key free route.

The worker never calls Codex or Claude automatically because their available free capacity is not verified by the Hub. It does not use paid APIs, buy credits, upgrade plans, or switch to a paid fallback. Provider readiness is not a numeric quota guarantee; 429/capacity errors stop the request. No automatic retry is performed.

ChatGPT, Grok and Gemini are not currently registered as DGM-HUB provider adapters. The status endpoint reports them as not integrated rather than pretending they are available. They require separate, legitimate adapters and their own free-capacity checks.

## Data minimization and safety

- Only the current user goal and a short capability-boundary explanation are sent to the Hub.
- No source files, repository contents, prior conversation history, credentials, cookies, or tokens are transmitted.
- Requests that look like they contain credentials are blocked before persistence or provider contact.
- External responses are stored with provider/task provenance, marked untrusted, and sent to the internal review queue.
- The result cannot authorize code edits, commands, deployment, or a reusable memory lesson.
- An ambiguous worker restart changes an in-flight request to `BLOCKED_RESTART`; it is never replayed.
- Repeated identical requests within 24 hours reuse the previous request/result instead of calling providers again.

## Controls

- `GET /runtime/auto-help` — local-client status and bounded recent history.
- `POST /runtime/auto-help/start` — operator-only start.
- `POST /runtime/auto-help/stop` — operator-only pause.
- Set `DGM_AUTONOMY_HELP_ENABLED=1` and `DGM_AUTONOMY_HELP_PROVIDERS=kilo,llm7` before runtime startup to enable the worker.

The worker is started by the DGM-MAT runtime only when explicitly enabled. The default remains off for tests and development.
