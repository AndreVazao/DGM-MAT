# Mobile mission routing — validation report

**Date:** 2026-11-03  
**Branch:** `fix/mobile-mission-routing-2026-11-03`  
**Base:** `19eea58` — DGM-MAT governed specialist integration

## Changes

- The mobile conversation service now uses the mission engine's authoritative `classify_mission_intent` decision before creating a mission.
- Supported read-only requests can create missions even when the lightweight chat classifier labels them as ordinary chat/status.
- Local audit/analyze/review verbs are mapped to the bounded local-research handler only when a local repository/project/code/docs target is present.
- "Estado do DGM-MAT" maps to the fixed read-only system summary.
- Mixed read/write requests are rejected as unsupported.
- Unsupported repair, implementation, deployment, external research and persistent-memory requests remain in the conversation only; no mission or queue action is created.
- Repair, implementation, synchronization, deployment and destructive language now carry an approval-required signal in the lightweight intent result.
- The conversation response and metadata expose mission decision, mission ID/status, queue action status and approval requirement. It distinguishes approval, execution, completion, failure and queued-for-approval states and does not claim completion at mission creation.

## Automated validation

- Python compileall passed for changed runtime and test modules.
- `git diff --check` passed.
- Focused suites: **62 passed** across:
  - `tests/mobile_runtime/test_mobile_runtime.py`
  - `tests/autonomy/test_mission_intent_router.py`
  - `tests/autonomy/test_read_only_diagnostic_missions.py`
  - `tests/autonomy/test_mission_result_terminal_guard.py`
  - `tests/autonomy/test_mission_system.py`
  - `tests/test_live_mission_diagnostic.py`

Coverage includes:
- read-only repository inventory routed to its registered handler;
- local DGM-MAT audit routed to local-only research and architecture analysis routed to the architecture-summary handler;
- DGM-MAT status routed to system summary;
- GitHub worktree sync held for operator approval;
- repair/implementation and mixed read/write requests not creating missions;
- external research and memory requests not claiming unsupported work;
- destructive intent remaining approval-gated.

Two existing `SyntaxWarning: invalid escape sequence '\\.'` warnings remain in `core/operations/command_executor.py`; that file was not changed by this branch and the test suite passed.

## Safety and deployment boundary

- All mission-engine calls in the new mobile-routing tests were mocked; no production mission or queue action was created.
- No repository files were changed outside this isolated worktree.
- The active DGM-MAT API process on port 8181 was not restarted.
- The Hub responder PR #31 is merged, and its pilot smoke test succeeded, but the active Hub on port 8770 still runs the previous local checkout.
- Local inference remains unavailable under the current free-memory level (~515 MB versus the 1.2 GB threshold); the deterministic response path remains in use.
- Generic code-editing execution is still not implemented. Unsupported mutations remain blocked rather than being routed to a fictitious executor.
