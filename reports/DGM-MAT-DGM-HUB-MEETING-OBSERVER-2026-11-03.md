# DGM-MAT - DGM-HUB passive meeting observer

**Date:** 2026-11-03
**Branch:** `feat/dgm-hub-meeting-observer-2026-11-03`
**Base:** DGM-MAT main after PR #158 and #165; commit `19eea585c86a0cda2eae7af033f673ead1a1a6e0`
**Issue:** #159 - DGM-HUB meeting learning and decision memory

## Objective

Capture the real DGM-HUB MultiChat room without taking over the room, sending messages, starting providers, or changing Hub state. Persist the original event provenance so later meeting summaries and explicit operator decisions can be reconstructed.

## Verified source contract

Live local Hub endpoint: http://127.0.0.1:8770

Current history contract (DGM-HUB issue #27, PR #30, merged as b46b8329f74e0d8e26a6a054235c14c6728664e0):

- GET /api/history?after=<seq>&limit=500 returns stable event_id, monotonic seq, next_cursor, has_more and total_events.
- user_message, provider_response and provider_error events carry the same task_id.
- Task results/status persist in SQLite across Hub restart; queued/running tasks are marked interrupted rather than re-executed.
- Legacy JSONL entries are migrated with deterministic event IDs and marked correlation_status=legacy_unlinked when no historical task relationship exists.
- The old GET /api/history?limit=500 latest-window contract remains compatible.

The original live capture on 2026-11-03 predates this Hub contract and therefore observed only conversation-level correlation. The DGM-MAT observer has now been updated to consume the new cursor and identity fields; the active Hub runtime has not yet been restarted, so live cursor operation against the new server has not been claimed.

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

The capture returned HTTP 200 from the pre-contract local history endpoint. The temporary database was discarded after the test. A background-thread test performed two polling passes: the first inserted 52 events across 15 conversations; the second recognized all 52 as duplicates. The observer then stopped cleanly, with zero provider calls and zero messages sent. This is historical evidence for the original bounded observer, not a claim that the new cursor API was live at that time.

## Automated validation

- Original observer baseline: 99 passed (2026-11-03).
- Refreshed main + observer + Hub + recovery + inventory integration suite: 172 passed in 17.06s.
- Focused observer API, store, cursor pagination, legacy database migration and atomic decision suite: 20 passed in 4.44s.
- Cursor regression reads four events across two pages and verifies persisted cursor, stable Hub IDs, source_seq, task_id and provider-error classification.
- A schema-v1 DGM-MAT observer database is upgraded in place; when a migrated Hub event matches the old source fingerprint, the existing row is upgraded to the stable Hub event ID rather than duplicated.
- A Hub journal reset (saved cursor greater than current total) fails closed and requires manual reconciliation; the observer never rewinds automatically.
- compileall and changed-source git diff --check passed.
- Existing warnings: two Python invalid-escape SyntaxWarnings and FastAPI on_event deprecation warnings. They are unrelated to the cursor implementation.
- DGM-HUB's unrelated full-suite import/port blockers are tracked separately in DGM-HUB issue #29.

## Known limitations / next gate

1. New Hub events now carry stable event_id, seq and task_id; historical events remain legacy_unlinked because their original task relationships cannot be reconstructed safely.
2. Cursor pagination resumes from the last committed page and processes up to 10 × 500 events per capture pass. If a backlog remains, the next pass resumes from the persisted cursor. The old Hub API fallback remains visibly partial and warns when its 500-event window is saturated.
3. If the Hub journal is reset and its total sequence falls below the saved cursor, capture stops and requires manual reconciliation; it does not rewind and risk silently duplicating or skipping records.
4. The observer schema migration preserves existing fingerprint rows and upgrades them in place when the corresponding stable Hub event arrives. Stored text remains redacted; the source Hub journal is never rewritten.
5. Proposals are recorded only when explicitly identified and linked to a provider response/error event from the same meeting. No automatic classifier can mark a proposal accepted.
6. Decisions are stored only after explicit authenticated operator confirmation. No provider consensus or model output can create a confirmed decision.
7. This phase does not generate AI summaries, choose a solution, chair meetings, dispatch tasks, edit projects, or execute patches.
8. A live end-to-end cursor capture against the new Hub runtime remains pending a controlled Hub restart. The active Hub process was intentionally not restarted during this implementation.

## Safety boundaries

- Hub base URL is restricted to HTTP loopback port 8770; environment proxies are disabled and redirects are refused.
- Capture uses GET only.
- No provider is enabled, started, retried, or called by the observer.
- No Hub chat messages are sent.
- All captured provider text remains untrusted.
- The authoritative DGM-MAT checkout and the active, uncommitted `C:\AI\DGM-HUB-MultiChat` working tree were left untouched.
- DGM-HUB issue #27 contract is merged; DGM-MAT PR #160 remains unmerged. No active Hub or DGM-MAT runtime restart/promotion has been performed.