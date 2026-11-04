# DGM-MAT — Durable Mission Queue Audit

**Date:** 2026-11-04  
**Scope:** Read-only inspection of the active local SQLite queue and mission checkpoint files.  
**Database:** `storage/runtime/temp/dgm_mat.db`  
**Mission checkpoints:** `storage/runtime/missions/mission_*.json`

## Executive result

The queue contains **1,065** durable actions. Of these, **801** are still `QUEUED`; all 801 have `is_approved = false`. Every queued row is a `MISSION_EXECUTION` action.

The queue worker only claims actions in `APPROVED` state with `is_approved = true`. Therefore, the 801 queued rows were not eligible for automatic execution at the time of this audit.

No queue row was approved, rejected, deleted, replayed or otherwise modified during this inspection.

## Queue state

| Queue status | Approved flag | Rows |
|---|---:|---:|
| COMPLETED | true | 117 |
| FAILED | true | 73 |
| QUEUED | false | 801 |
| REJECTED | false | 74 |
| **Total** | | **1,065** |

All 801 queued rows have action type `MISSION_EXECUTION`. Their database timestamps (stored without timezone metadata) range from **2026-10-07 07:35:01** to **2026-11-03 19:47:22**.

## Reconciliation against mission checkpoints

The current mission checkpoint directory contains **570** mission files:

| Checkpoint status | Files |
|---|---:|
| FAILED | 557 |
| COMPLETED | 9 |
| QUEUED | 4 |
| **Total** | **570** |

The 801 queued actions reconcile as follows:

| Current checkpoint evidence | Queued actions |
|---|---:|
| Matching mission checkpoint is FAILED | 378 |
| Matching mission checkpoint is QUEUED | 4 |
| No matching file in the current mission checkpoint directory | 217 |
| Test-fixture identifiers `mission_contract` / `mission_result` | 202 |
| **Total** | **801** |

There are 601 distinct mission identifiers among the queued actions. The 202 test-fixture rows consist of **101** copies for `mission_contract` and **101** copies for `mission_result`. Excluding those two fixture identifiers, 217 action identifiers have no matching checkpoint file in the current mission directory.

The 217 unmatched identifiers are classified as **unreconciled**, not automatically stale: they may require investigation against archived checkpoints, earlier storage locations or historical event records.

## Confirmed source of test contamination

The former `tests/contracts/test_queue_boundary.py` instantiated the production `SafeActionQueue` singleton and used the shared `SessionLocal`. Each test run inserted two persistent `MISSION_EXECUTION` records into the developer's runtime database.

This explains the 202 fixture rows accumulated over 101 executions.

**Correction merged:** PR [#173](https://github.com/AndreVazao/DGM-MAT/pull/173) now creates a temporary SQLite database and a fresh queue singleton for each contract test. It also adds the DGM-Contracts checkout to focused PR validation so the tests run in CI.

Validation evidence:
- Focused PR Validation workflow **#116**: success.
- Local focused contract tests: **2 passed**.
- Production queue count before and after the local test run: **1,065 → 1,065**.

The historical 202 fixture rows remain in the queue for auditability. They were not deleted or silently rewritten.

## Operational decisions

1. **Do not bulk-approve the 801 rows.** They are all unapproved and include terminal, unmatched and test-generated records.
2. **Do not bulk-delete or bulk-reject them.** Preserve the existing audit trail until each class is reconciled.
3. Keep the four actions associated with currently QUEUED mission checkpoints pending operator review.
4. Investigate the 378 actions whose mission checkpoints are FAILED. A failed checkpoint must not be replayed merely because its queue row remains QUEUED.
5. Investigate the 217 unmatched mission identifiers against archived checkpoints and historical event records.
6. Retain the 202 test-fixture rows as historical evidence; the test-isolation fix prevents further accumulation.

## Related telemetry correction

PR [#174](https://github.com/AndreVazao/DGM-MAT/pull/174) was merged to correct `missions_active` in `/runtime/status` and `/runtime/autonomy`. It now counts only missions in `RUNNING`, rather than the complete historical mission index.

## Audit limitations

- This audit counted rows and inspected payload structure, approval flags, timestamps and checkpoint statuses. It did not reproduce mission goals or read credentials.
- The 217 unmatched identifiers were checked against the current `runtime/missions` directory only.
- No claim is made that every historical mission has been recovered.
- The Snyk PR check was reporting an external service error; it did not return a vulnerability result.

**Conclusion:** the 801 queued actions are not a valid autonomous workload. Keep them unapproved until reconciliation is complete. The confirmed test-contamination source is now fixed for future runs.
