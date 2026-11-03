# DGM-MAT ↔ DGM-HUB MultiChat — integration contract

**Date:** 2026-11-03  
**Implementation branch:** `feat/dgm-hub-multichat-agent-bridge-2026-11-03`  
**Hub checkout:** `C:\AI\DGM-HUB-MultiChat`  
**Hub branch:** `feature/dgm-hub-multichat-cockpit`

## Decision and authority

DGM-HUB MultiChat remains an independent local provider room and transport. It is not merged into DGM-MAT and is not silently promoted to an architectural authority.

The operator remains the room leader. DGM-MAT remains an observer in the Hub room. DGM-MAT may now perform a narrowly scoped, operator-requested consultation against selected external participants and bring the responses into its existing specialist-collaboration workflow. This does **not** grant DGM-MAT autonomous room leadership, autonomous provider selection, or permission to change provider participation.

The existing Hub participant set is:

| Hub ID | Transport observed | Permitted DGM-MAT role |
|---|---|---|
| `codex` | Codex Free local CLI launcher | Engineering/code-architecture consultation |
| `claude` | Claude Code CLI 2.1.112 through local FCC | Senior engineering review/diagnosis |
| `kilo` | Kilo Gateway, free-model route | Independent reasoning/design critique |
| `llm7` | Anonymous LLM7 endpoint, configured model `gpt-oss:20b` | Architecture/requirements/test-strategy consultation |
| `dgm_mat` | Existing Hub observer hook | Observation only; excluded as a target to avoid recursive calls |
| `ollama` | Local Ollama | Disabled and excluded from this integration |

The Hub's local API is `http://127.0.0.1:8770`. The FCC listener is restricted to `127.0.0.1:8082`. The DGM-MAT bridge rejects remote, HTTPS, credential-bearing, and non-loopback Hub URLs.

## Runtime path

1. An authenticated DGM-MAT operator submits a bounded goal, authorized context, selected provider IDs and explicit confirmation that the selected providers are currently being used only in their free modes.
2. DGM-MAT creates one durable `SpecialistCollaborationStore` packet per selected provider **before** calling the Hub.
3. The bridge checks the Hub provider inventory. It does not start, enable, or repair a provider.
4. The bridge posts one consultative request to `POST /api/chat` and polls the correlated Hub task.
5. Only results with Hub task correlation and `status=ok` are accepted into the collaboration ledger.
6. DGM-MAT calls `MissionEngine.record_specialist_result`. Each answer is marked `RESULT_RECEIVED`, remains untrusted, and triggers the existing independent-review intake to `agent:bug-hunter`.
7. Results are not validated lessons, are not executable patches, and are not applied to repositories. Independent review and real local tests remain mandatory.

## API contract

- `GET /governance/agents/hub/status`: operator-only, read-only Hub status; sends no model prompt.
- `POST /governance/agents/hub/consult`: operator-only, bounded one-shot consultation.
- Request fields: `goal`, `context`, `providers`, `free_capacity_confirmed`.
- Allowed providers: `codex`, `claude`, `kilo`, `llm7`.
- One to four providers per request; no implicit provider discovery.
- `free_capacity_confirmed=true` is an explicit operator attestation. The Hub API does not expose numeric remaining quotas, so DGM-MAT does not claim that quota was independently measured.
- Hub/model errors, rate limits, timeouts and unavailable providers stop the request. No automatic retry, paid fallback, account upgrade or credit purchase.
- The API returns transport model identity only when the Hub response includes a `model` field. It never trusts a model's own textual identity claim.

## Zero-cost and quota boundary

The existing DGM-MAT FREE-ONLY / PAID-DENY policy remains in force. The bridge is deliberately consultative and operator-initiated. It does not register these Hub routes as generic production `ProviderBase` adapters, because the Hub does not expose atomic remaining-quota reservation.

The operator's free-mode confirmation is recorded as an attestation, **not** as a provider quota measurement. The Hub does not expose remaining quota for Codex, Claude Code, Kilo or LLM7. If a provider reports a rate/capacity error, DGM-MAT records a paused collaboration and stops. No paid route is available as a fallback.

The current Hub implementation uses:
- Kilo model routing constant `openrouter/free`; actual response model IDs are returned by the Hub.
- LLM7 model constant `gpt-oss:20b`, with anonymous/no-key transport.
- Codex Free CLI launcher.
- Claude Code CLI through FCC. FCC's configured backend must be checked separately; the CLI product name is not proof of the underlying model.

## Smoke-test evidence — 2026-11-03

A single operator-initiated Hub request targeted all four external participants plus the DGM-MAT observer. The Hub returned task ID `b6fb8005-b1b6-47ec-96b9-0940ba495b98`. All five participants completed:

| Participant | Hub result | Duration | Verified transport model |
|---|---:|---:|---|
| Codex | `ok` | 60.54 s | Not reported |
| Claude Code/FCC | `ok` | 54.64 s | Not reported by Hub response |
| Kilo | `ok` | 58.01 s | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` |
| LLM7 | `ok` | 5.84 s | `gpt-oss:20b` |
| DGM-MAT | `observer` | 0 s | Not applicable |

Important provenance finding: the LLM7 response text claimed “GPT-4”, while the Hub transport metadata identified `gpt-oss:20b`. The transport metadata is retained as the model identity; provider self-claims are untrusted. The Claude Code response self-claimed Claude Sonnet 4.6, but the Hub did not return a transport model ID, so that claim is not verified. The Hub's FCC configuration must be treated as a separate model backend.

All external agents were asked to be consultative and to declare no file edits or command execution. Their responses are evidence of successful request/response transport, not proof of their claims or of code execution. DGM-MAT's observer response explicitly confirmed it had not yet been connected to its authenticated conversational engine at the time of the smoke test.

## Security and limits

- DGM-MAT bridge permits loopback only; no remote Hub address can be configured.
- DGM-MAT API route requires the operator session scope.
- The bridge never starts or stops Hub providers.
- The bridge never sends the DGM-MAT repository path as a writable workspace.
- Hub responses are stored as untrusted specialist output; prompt injection and factual errors remain possible.
- Provider result text is bounded and the existing collaboration store rejects secret-like content.
- DGM-MAT does not become room chair; no autonomous polling, recurring provider calls or takeover behavior is implemented.

## Next gate: controlled coding execution

The next increment must make a separate, isolated worktree-based execution path. A provider may propose a patch; DGM-MAT must stage it in a disposable branch/worktree, run fixed allowlisted tests, preserve a diff and logs, obtain independent review, and request operator approval before promotion. Provider text alone must never be applied as a patch. Do not enable agent write mode in the Hub until explicit sandbox and permission behavior is independently tested.


## Local integration validation addendum — 2026-11-03

The DGM-MAT API bridge has now been exercised against the live local Hub from an authenticated operator TestClient. Kilo and LLM7 returned usable consultation results and were persisted as untrusted specialist results; Codex and Claude Code timed out at their current Hub CLI limits and were paused. A later LLM7 request returned HTTP 429 and was paused without retry or paid fallback. The API now reports mixed outcomes as `partial`, never as fully completed.

Windows validation: compileall passed; 56 focused tests passed; `git diff --check` passed. The real MissionEngine specialist intake was separately verified to write a correlated message to the SQLite-backed `agent:bug-hunter` inbox. Full commands and exact outcomes: [DGM-MAT ↔ DGM-HUB local validation report](../../reports/DGM-MAT-DGM-HUB-BRIDGE-VALIDATION-2026-11-03.md).

The integration remains consultation-only. No provider has permission to edit files or execute commands through this bridge. The next gate is a separate isolated-worktree patch proposal/execution pipeline with independent QA and explicit approval.
