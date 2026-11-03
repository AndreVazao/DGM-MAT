# Telescope metadata-only adapter — validation report

Date: 2026-11-03
Repository: AndreVazao/DGM-MAT
Worktree: C:\ProgramasGodMode\_worktrees\ai-conversation-inventory-2026-11-03
Branch: feat/telescope-metadata-only-2026-11-03

## Finding

The previous adapter serialized the complete `tele sessions get --json` payload into ConversationRecord.content and metadata. The local Telescope schema includes fields for last-message previews, full turns and an opaque metadata object. Persisting that raw payload could therefore ingest private conversation content or secrets.

## Change

The adapter now projects both list and detail responses onto an explicit metadata allowlist:
- session_id, agent_id, git_branch, status, started_at, ended_at, turn_count and duration_ms;
- project is derived only from the final directory component of cwd;
- absolute cwd, git_repo, last_message, turns, raw metadata and all unknown fields are discarded;
- ConversationRecord uses a generated non-content title and a metadata-only content policy;
- invalid IDs, missing executable, malformed JSON, process errors and CLI timeouts fail closed.

This is not a transcript importer. Full-session content remains unavailable through this adapter.

## Validation

Executed on Windows Python 3.12:
- `tests/test_telescope_metadata_only.py`
- `tests/test_ai_source_inventory.py`
- `tests/api/test_recovery_local_source_inventory.py`
- Result: 11 tests passed.
- `python -m compileall -q core tests`: passed.
- `git diff --check`: passed.

The test fixtures deliberately include fake prompt previews, full turns, API tokens, authenticated repository URLs and absolute user paths. Assertions verify that none reach the returned records.

## Safety / scope

- No real Telescope session content was imported or persisted.
- No provider account, cookies, browser tokens or IndexedDB contents were accessed.
- No running DGM-MAT or DGM-HUB service was restarted.
- Changes are isolated in the branch above; no merge or publication is claimed.
