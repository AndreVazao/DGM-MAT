# DGM-HUB MultiChat — live provider smoke test

**Date:** 2026-11-03  
**Hub task:** `b6fb8005-b1b6-47ec-96b9-0940ba495b98`  
**Conversation:** `dgm-mat-provider-integration-smoke-2026-11-03`  
**Hub URL:** `http://127.0.0.1:8770`  
**FCC URL:** `http://127.0.0.1:8082`

## Results

| Participant | Status | Duration | Model from transport metadata |
|---|---:|---:|---|
| Codex | `ok` | 60.54 s | Not reported |
| Claude Code/FCC | `ok` | 54.64 s | Not reported |
| Kilo | `ok` | 58.01 s | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` |
| LLM7 | `ok` | 5.84 s | `gpt-oss:20b` |
| DGM-MAT observer | `observer` | 0 s | N/A |

All five target results were returned and the Hub task reached `done=true`.

## Proven

- Hub API accepted a multi-provider request and returned a correlated task ID.
- Codex, Claude Code/FCC, Kilo and LLM7 each returned a non-empty response with `status=ok`.
- DGM-MAT's observer hook was invoked and returned its explicit observer response.
- The Hub API reported all four external providers as `enabled=true`, `online=true`, `ready=true` at the time of the test.
- FCC listener was observed on `127.0.0.1:8082`, not a wildcard interface.
- No model identity was inferred from free-form provider text.

## Provenance warnings

- LLM7 response text claimed GPT-4, but Hub transport metadata identified `gpt-oss:20b`. Treat the textual claim as incorrect/untrusted.
- Claude Code response text claimed Claude Sonnet 4.6, but Hub response metadata did not expose a model ID. The claim is unverified; FCC backend configuration is authoritative for the actual model route.
- Codex did not expose a model ID in the Hub response.
- Hub exposes no numeric remaining quota for these providers. The successful smoke test proves reachability and response, not unlimited capacity or a numeric remaining free quota.

## Safety

The prompt explicitly required consultative responses only, no file edits, no command execution, and a declaration of whether those actions occurred. All external agents stated they had not edited files or run commands. This is a provider self-report, not an independent OS-level audit of their subprocesses.

No DGM-MAT repository files were sent as a writable workspace. No Hub provider was enabled/disabled by this smoke test. No automatic retry or paid fallback was used.

## Conclusion

The four external provider transports are functional for operator-initiated consultation through DGM-HUB. DGM-MAT's Hub observer hook is functional. The DGM-MAT-to-Hub API bridge and durable specialist-result intake are implemented in the associated feature branch; they still require local Windows test evidence before merge. This does not yet prove autonomous code editing or self-repair.
