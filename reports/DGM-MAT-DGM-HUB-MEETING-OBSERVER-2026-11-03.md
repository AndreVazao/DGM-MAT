# DGM-MAT - DGM-HUB passive meeting observer

**Date:** 2026-11-03
**Branch:** `feat/dgm-hub-meeting-observer-2026-11-03`
**Base:** DGM-MAT PR #158 head `70fc8e82bc7486f2e82caa30100ec2025ba5f7a4`
**Issue:** #159 - DGM-HUB meeting learning and decision memory

## Objective

Capture the real DGM-HUB MultiChat room without taking over the room, sending messages, starting providers, or changing Hub state. Persist the original event provenance so later meeting summaries and explicit operator decisions can be reconstructed.

## Verified source contract

Live local Hub: `http://127.0.0.1:8770`
Read-only endpoint: `GET /api/history?limit=500`
Hub journal: `C:\AI\DGM-HUB-MultiChat\runtime\multichat\conversation.jsonl`

The current Hub journal contains `user_message` and `provider_response` events with timestamps, `conversation_id`, provider identity and text. The API exposes a bounded latest-500 event window. The current journal does **not** expose a stable event ID or `task_id`; the observer therefore derives an immutable SHA-256 fingerprint from each source event and reports correlation as conversation-only rather than inventing task correlation.

The Hub task result map is process-memory based. A Hub restart can lose task status/results even though the JSONL journal remains on disk.

## Implementation

- `core/organization/dgm_hub_meeting_observer.py`: loopback-only GET client (5-second poll interval), proxy disabled, redirects refused, SQLite event ledger, stable source fingerprints, idempotent ingest, participant grouping, objective/target extraction, and secret-pattern redaction.
- `core/api/dgm_hub_agents_api.py`: operator-authenticated observer status/capture/start/stop, meeting list/detail, explicit proposal capture and explicit decision recording.
- `core/api/security_policy.py`: all new routes classified as operator-only.
- `core/api/api_server.py`: passive observer starts on API startup by default; `DGM_HUB_OBSERVER_ENABLED=0` disables it. Shutdown stops the polling thread.
- SQLite location: `storage/runtime/tasks/hub_meeting_observer.sqlite3` (under the configured DGM-MAT storage root).
- Meeting decisions are also recorded in the existing `ConversationKnowledgeStore` tables in the same SQLite database. A decision is `confirmed_by_user=true` only when an authenticated operator calls the decision endpoint with `confirm=true`. Agent agreement is never interpreted as approval.

### API surface

All endpoints require an authenticated operator session:

- `GET /governance/agents/hub/observer/status`
- `POST /governance/agents/hub/observer/capture` - one bounded capture pass
- `POST /governance/agents/hub/observer/start`
- `POST /governance/agents/hub/observer/stop`
- `GET /governance/agents/hub/meetings`
- `GET /governance/agents/hub/meetings/{conversation_id}`
- `POST /governance/agents/hub/meetings/{conversation_id}/proposals`
- `POST /governance/agents/hub/meetings/{conversation_id}/decision`

Proposal records require a source event belonging to the same meeting and of kind `provider_response`. Decision records require `confirm=true`, a valid operator session, and any referenced proposal IDs must belong to that meeting. The operator's rationale and accepted/rejected proposal IDs are preserved as decision evidence.

## Live read-only capture

A temporary SQLite database was used so the production DGM-MAT storage and the Hub files were not modified.

| Measurement | Result |
|---|---:|
| Hub history events received | 52 |
| Events inserted | 52 |
| Duplicate events | 0 |
| Invalid events | 0 |
| Distinct conversations | 15 |
| Hub history window saturated | No |
| Messages sent to Hub | 0 |
| Provider calls initiated | 0 |

The capture returned HTTP 200 from the local history endpoint. The temporary database was discarded after the test. A background-thread test performed two polling passes: the first inserted 52 events across 15 conversations; the second recognized all 52 as duplicates. The observer then stopped cleanly, with zero provider calls and zero messages sent.

## Automated validation

- `compileall`: passed.
- Full focused regression (PR #158 baseline, observer/API/security and knowledge-store tests): **99 passed in 10.54s**.
- The run includes three atomicity/confirmation tests for the decision and proposal ledger.
- `compileall` and `git diff --check` both passed.
- FastAPI `on_event` deprecation warnings remain in the existing application lifecycle and the newly added hooks; this is not a test failure and should be migrated to a lifespan handler in a separate bounded change.
- Existing `command_executor.py` invalid-escape `SyntaxWarning` is unrelated and unchanged.

## Known limitations / next gate

1. Task-level correlation remains incomplete because the Hub history contract does not include `task_id` or a source event ID. No synthetic task IDs are created. A separate DGM-HUB contract change is needed.
2. The Hub history endpoint returns only the latest 500 events. If that window is saturated, the observer raises a visible warning that older unseen events may be missing. It does not claim complete capture.
3. The observer stores sanitized event payloads and their SHA-256 source fingerprints. Secret-like patterns are redacted in stored text; the Hub source journal is never rewritten.
4. Proposals are recorded only when explicitly identified and linked to a provider response. No automatic classifier can mark a proposal accepted.
5. Decisions are stored only after an explicit authenticated operator confirmation. No provider consensus or model output can create a confirmed decision.
6. This phase does not generate AI summaries, choose a solution, chair meetings, dispatch tasks, edit projects, or execute patches.

## Safety boundaries

- Hub base URL is restricted to HTTP loopback port 8770; environment proxies are disabled and redirects are refused.
- Capture uses GET only.
- No provider is enabled, started, retried, or called by the observer.
- No Hub chat messages are sent.
- All captured provider text remains untrusted.
- The authoritative DGM-MAT checkout and the active, uncommitted `C:\AI\DGM-HUB-MultiChat` working tree were left untouched.
- No merge or promotion has been performed.