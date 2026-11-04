# DGM-MAT Local Mission Research — Unicode and Evidence Ranking

Date: 2026-11-04
Branch: feat/unicode-local-research-2026-11-04
Base: origin/main (15bb570)

## Problem observed

A real read-only mission investigating SafeActionQueue and MissionEngine completed successfully, but its evidence quality was insufficient:
- Portuguese words containing diacritics were split into fragments by the ASCII-only tokenizer.
- Generic verbs and fragments consumed the eight-keyword budget, displacing technical identifiers.
- Search traversal spent its bounded file budget before inspecting the owning autonomy/runtime modules.
- Repeated matches from one file could dominate the eight-result response.

A completed mission was therefore not equivalent to a useful investigation.

## Changes

- Normalize query text and source lines with Unicode NFKD, case-folding and combining-mark removal.
- Expand Portuguese stop words and remove common research verbs from the keyword budget.
- Rank repeated and specific technical terms ahead of generic short fragments, retaining query order as a tie-breaker.
- Prioritize relevant autonomy, runtime, operations and organization directories for mission/queue/executor investigations.
- Deduplicate paths when the broad repository walk follows priority directories.
- Weight exact technical terms and matching file paths during evidence ranking.
- Exclude the research engine's own source file from results to avoid self-referential matches.
- Limit results to two lines per file so one source cannot monopolize the result set.
- Preserve existing local-only boundaries: no network calls, no command execution, bounded files/time/output, and secret redaction.

## Verification

Focused tests:
`python -m pytest -q tests/autonomy/test_mission_research.py tests/autonomy/test_read_only_diagnostic_missions.py`

Result: **18 passed**.

Additional checks:
- `python -m compileall -q core/autonomy/mission_research.py` — passed.
- `git diff --check` — passed.
- Real repository query scanned 250 files within the existing bounded search policy and returned evidence from:
  - `core/runtime/safe_action_queue.py`
  - `core/autonomy/mission_engine.py`
- The real query reported `external_calls=0` and `commands_executed=0`.

Existing SyntaxWarning notices from `core/operations/command_executor.py` remain unrelated and that file was not changed.

## Safety and rollout

This change improves evidence retrieval only. It does not add a generic executor, enable write access, approve new action types, alter SafeActionQueue, or modify runtime state.

The patch is isolated in a clean worktree and is not active in the running DGM-MAT process. Merge and a separately reviewed deployment are required before the live runtime can use it.
