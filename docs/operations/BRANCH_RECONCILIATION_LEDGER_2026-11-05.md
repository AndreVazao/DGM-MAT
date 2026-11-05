# Branch reconciliation ledger — 2026-11-05

**Scope:** Seven active project repositories.  
**Method:** GitHub branch enumeration plus compare of each non-default branch against main.  
**Status:** Initial complete name inventory and commit-distance audit; file-level review, CI verification and branch deletion are still pending.  
**Policy:** Never delete a branch containing unique work until its useful changes are integrated and verified. Keep main in every repository.

## Executive result

- Repositories audited: 7
- Non-main branches enumerated: 57
- Branches compared to main: 57 (one branch comparison returned 404 due a stale/mismatched ref name; the actual PR head ref was separately compared successfully)
- This is not yet a deletion authorization list. Ahead/behind counts identify work to inspect; they do not prove that a branch is safe to merge or delete.
- No branch was deleted in this audit.

## DGM-MAT

| Branch | Ahead | Behind | Initial classification |
|---|---:|---:|---|
| audit/programming-department-readiness-2026-10-22 | 48 | 52 | Unique development department work; inspect and port |
| feat/bounded-worktree-execution-2026-11-04 | 4 | 2 | Unique execution-fabric work; inspect/tests |
| feat/chatgpt-recovery-import-api-2026-11-03 | 6 | 36 | Recovery API/import work; reconcile with current recovery branch |
| feat/external-agent-readiness-probe-2026-11-03 | 17 | 36 | Unique readiness/governance work; inspect/tests |
| feat/telescope-metadata-only-2026-11-03 | 2 | 33 | Metadata inventory work; compare with current recovery implementation |
| fix/frozen-external-runtime-dependencies-2026-11-04 | 1 | 11 | PR #203; currently conflicts with recovery base, do not merge yet |
| fix/backup-first-executor-rebased-2026-11-05 | closed/superseded | — | PR #214 closed without merge; branch retained for audit |
| fix/backup-first-executor-dirfd-2026-11-05 | 7 | 7 | Draft PR #217; POSIX no-follow dirfd + pinned root identity, symlink/root-swap regressions; Linux #256 passed (15/1 skip), Windows Guard #4 passed (9/7 POSIX-only skips); Windows writes fail closed pending issue #218 native backend |
| fix/backup-first-executor-win32-2026-11-05 | closed/superseded | — | PR #219 closed without merge to remove 78-commit history; branch retained for audit. Its six executor/workflow/test/report files were carried forward unchanged to the clean branch |
| fix/backup-first-executor-win32-clean-2026-11-05 | 1 | 1 | Draft PR #220; one commit, six files. Fresh Windows Guard #73 passed (38 passed, 8 POSIX-only skipped) and Focused Validation #330 passed on exact PR head. Snyk private-test quota error; CodeRabbit free-review limit reached; local Windows 10 acceptance remains open |
| fix/conversation-completeness-evidence-2026-11-05 | merged | 0 | PR #216 merged as `31608eb`; bounded virtualized top-loading evidence added; live provider acceptance remains open |
| test/browser-virtualized-history-fixtures-2026-11-05 | closed/superseded | — | PR #221 closed without merge to remove iterative history; source branch retained for audit. Five browser/API/workflow/test files carried forward unchanged to clean branch |
| test/browser-virtualized-history-clean-2026-11-05 | 1 | 0 | Draft PR #222; one commit, five files. Chrome Extension Validation #103 and Focused PR Validation #354 passed on exact head; artifact #13435428666. Seven deterministic fixtures cover provider selectors, virtualized windows, order, limits and fail-closed DOM mismatch. Live authenticated UI acceptance remains open |
| recovery/dgm-mat-overnight-2026-11-05 | 3 | 1 before this ledger update | Active recovery branch; PR #204 targets main |

## DGM-MAT-Mobile

| Branch | Ahead | Behind | Initial classification |
|---|---:|---:|---|
| recovery/dgm-mat-mobile-consolidation-2026-11-05 | 0 | 0 | Identical to main; candidate for deletion after PR cleanup |
| test/maestro-android-smoke-2026-10-28 | 8 | 0 | Unique Android smoke workflow; PR #3 targets main and PR #4 duplicates same head against recovery |

PR #3 and #4 share head branch and commit f31b643355eedc23d14d774fac96091898d1e299. Merge the feature once after CI succeeds; close the duplicate PR after verifying the first merge.

## DGM-HUB

| Branch | Ahead | Behind | Initial classification |
|---|---:|---:|---|
| feat/configurable-dgm-mat-runtime-url-2026-11-03 | 3 | 1 | Unique launcher/runtime configuration; reconcile with PR #33/#34 |
| recovery/dgm-hub-consolidation-2026-11-05 | 1 | 1 | Recovery consolidation; inspect unique commit before cleanup |

## Office-Kit

| Branch | Ahead | Behind | Initial classification |
|---|---:|---:|---|
| feat/adapter-runtime-bridge | 7 | 14 | Unique adapter bridge and tests; PR #25 currently conflicts |
| feat/license-activation-registry | 16 | 1 | Unique licensing registry and tests; requires focused PR and CI |
| recovery/office-kit-consolidation-2026-11-05 | 1 | 0 | Recovery target; compare shows one commit but no file delta, inspect commit before deletion |

## VazaoSovereignTrader

| Branch | Ahead | Behind | Initial classification |
|---|---:|---:|---|
| audit/trading-integration-2026-10-22 | 0 | 87 | Behind-only; archive/verify before deletion |
| docs/adaptive-virtual-office-market-research-2026-10-19 | 2 | 130 | Unique research document; port if still authoritative |
| docs/audit-after-l2-replay-and-coinbase-guard | 0 | 69 | Behind-only; archive/verify before deletion |
| docs/audit-latest-main-marketdata-status | 5 | 75 | Unique audit document; reconcile against current status |
| docs/family-learning-and-trader-roadmap-2026-10-19 | 2 | 130 | Unique roadmap; port if still current |
| docs/open-source-patterns-and-audit-refresh | 2 | 62 | Unique architecture/audit docs; compare overlap |
| docs/recover-useful-roadmaps-2026-10-23 | 3 | 39 | Multiple useful roadmap docs; compare overlap with docs branches |
| docs/remote-conversational-cockpit-2026-10-19 | 1 | 130 | Unique cockpit document; port if still current |
| docs/virtual-office-exploded-mockup-2026-10-21 | 4 | 106 | Unique mockups/SVG assets; inspect and port |
| docs/vst-current-gates-2026-10-23 | 1 | 39 | Unique gate/status document; port if still current |
| feat/android-emulator-maestro-smoke-2026-10-27 | 3 | 36 | Unique Android workflow/flow/docs; compare with later APK fixes |
| feat/android-launcher-icon-2026-10-24 | 8 | 38 | Unique branding/build changes; reconcile with later branding branches |
| feat/approved-artwork-mobile-branding-2026-10-24 | 5 | 38 | Overlaps launcher/branding branches; reconcile file by file |
| feat/binance-spot-book-state-machine | 5 | 85 | Unique market-data state machine and tests; requires tests/review |
| feat/durable-research-leases-2026-11-05 | 0 | 2 | Behind-only; verify no unpushed/local work before deletion |
| feat/learning-vault-backup-manifest-2026-11-05 | 4 | 1 | Unique backup manifest code/docs/tests; recovery branch contains related work |
| feat/obscura-evaluation-lab-2026-10-29 | 5 | 18 | Unique evaluation workflows/docs; inspect provider/cost boundaries |
| feat/office-ceo-brand-plaque-2026-10-24 | 4 | 38 | Unique virtual-office prototype/doc changes; inspect |
| feat/okx-books-sequence-sync | 2 | 50 | Unique order-book sync changes; compare with synchronizer branch |
| feat/okx-books-synchronizer | 12 | 42 | Unique code/tests; overlaps sequence-sync branch; reconcile together |
| feat/vst-brand-consolidation-2026-10-27 | 1 | 34 | Branding/build/installer changes; overlaps other branding branches |
| feat/vst-unified-branding-2026-10-27 | 0 | 34 | Behind-only; verify before deletion |
| feat/windows-brand-icons-2026-10-24 | 9 | 38 | Unique Windows installer/icon changes; overlaps branding branches |
| fix/android-cockpit-scroll-2026-10-20 | 3 | 130 | Unique UI fix/doc; verify still applicable |
| fix/android-emulator-apk-path-2026-10-27 | 14 | 36 | Multiple useful Android/L2 fixes; compare with narrower fixes |
| fix/coinbase-book-fail-closed-invalid-event | 4 | 38 | Unique safety fix/tests; compare with broader APK/L2 branch |
| fix/unknown-latency-summary-null-2026-10-21 | 2 | 105 | Unique timing fix/tests; inspect |
| fix/websocket-timing-semantics-2026-10-20 | 0 | 121 | Behind-only; verify before deletion |
| fix/websocket-timing-semantics-2026-10-21 | 2 | 120 | Unique timing fix/tests; compare with later main |
| recovery/vazao-sovereign-trader-consolidation-2026-11-05 | 1 | 1 | Recovery branch; contains learning-memory backup work |
| test/l2-persistence-contract-main-2026-10-27 | 3 | 36 | Unique L2 persistence tests/docs; overlap with synchronized contract |
| test/l2-synchronized-persistence-contract-2026-10-27 | 7 | 38 | Unique L2 collector/tests/docs; reconcile with other L2 branches |
| work/mobile-virtual-office-demo-2026-10-28 | 116 | 31 | Large unique implementation; do not delete; needs staged review |
| work/mobile-virtual-office-demo-main-2026-10-28 | 6 | 31 | Unique mobile UI/startup changes; compare with larger work branch |
| work/strict-public-payload-json-2026-10-28 | 56 | 31 | Large unique provenance/public-payload changes; do not delete; needs staged review |

## VAZAO-EVSE-Platform

| Branch | Ahead | Behind | Initial classification |
|---|---:|---:|---|
| docs/tooling-capability-audit-2026-10-14 | 2 | 127 | Unique historical tooling docs; preserve if useful |
| feat/charger-hardware-v1-component-selection | 26 | 126 | PR #2; 14 engineering documents/SVG; selection gate remains provisional |
| recovery/vazao-evse-consolidation-2026-11-05 | 2 | 0 | Two recovery commits already ahead of main; contains PR #5/#6 recovery work |

## andreos-memory

| Branch | Ahead | Behind | Initial classification |
|---|---:|---:|---|
| continuity/dgm-advancement-review-2026-10-13 | 67 | 302 | Large unique continuity archive; PR #26; file-level deduplication required |
| continuity/pc-setup-2026-10-11 | 68 | 302 | PR #27 actual head ref; unique PC/DGM context; compare successful using exact PR head name |
| docs/tooling-capability-audit-2026-10-14 | 71 | 302 | PR #28; overlaps PR #26/#27; reconcile by file, not merge sequence |
| memory/vazao-sovereign-trader-pr376 | 0 | 416 | Behind-only; verify no unique content/local work before deletion |
| recovery/andreos-memory-consolidation-2026-11-05 | 7 | 1 | Recovery branch; contains six changed files plus one recovery commit; inspect before merge |

## Current open PR gates

| Repository / PR | Current status | Next action |
|---|---|---|
| DGM-MAT #203 | Not mergeable; frozen runtime dependency branch conflicts with recovery base | Rebase/port by focused PR only after comparing unique code/tests |
| DGM-MAT #204 | Mergeable; Focused PR Validation and Snyk status were pending at last check | Wait for CI/security result; no merge while pending |
| DGM-MAT #214 | Closed/superseded; no merge. Its original path-based backup executor remains blocked by TOCTOU | Retain branch for audit; use #220 for the Windows-native executor path |
| DGM-MAT #216 | Merged as `31608eb`; Focused PR Validation #243 and Chrome Extension Validation #79 passed | Complete live UI acceptance in #208 and provider-confirmed history-boundary work in #215 |
| DGM-MAT #217 | Draft; POSIX dirfd prototype, Windows mutation fail-closed | Reconcile with #220 after review; do not merge duplicate executor code |
| DGM-MAT #219 | Closed/superseded without merge; 78-commit history retained on branch for audit | Use clean PR #220; do not delete the source branch until #220 is accepted |
| DGM-MAT #220 | Draft; three commits, six files. Exact head passed Windows Guard #73 (38 passed, 8 POSIX-only skipped) and Focused PR Validation #330. Snyk private-test quota error; CodeRabbit free-review limit reached; local Windows 10 acceptance pending | Keep draft. Obtain independent review when quota resets, confirm backup-root ACL and durability assumptions, then perform local Windows 10 acceptance before MissionEngine integration |
| DGM-MAT #221 | Closed/superseded without merge; 14-commit history retained on source branch for audit | Use clean PR #222; do not delete the source branch |
| DGM-MAT #222 | Draft; one commit, five files. Chrome Extension Validation #103 and Focused PR Validation #354 passed; artifact #13435428666. Seven deterministic fixtures and API evidence gating are present; live provider acceptance remains open | Keep draft until code review and live authenticated UI acceptance; no provider may claim oldest-history confirmation until its evidence is allowlisted |
| DGM-MAT-Mobile #3/#4 | Same head commit; Maestro UI smoke run was in progress | Wait for one successful run, merge #3 once, close #4 duplicate |
| Office-Kit #25 | Not mergeable | Reconcile adapter bridge against current main and #26 recovery |
| VAZAO-EVSE #2 | Git mergeable, but engineering gate remains provisional | Review evidence and checks; do not treat as final component approval |
| andreos-memory #26/#27/#28 | All not mergeable and highly overlapping | File-level reconciliation and staged PRs |

## Deletion gate

A branch may be removed only when:
1. every unique commit is present in a verified destination branch or archived patch;
2. relevant tests/checks pass;
3. no open PR, release, deployment or local-only change depends on it;
4. the branch ledger records the destination commit and evidence.

Behind-only branches are candidates, not automatic deletions. Keep the default branch. No branch deletions were performed during this audit.
