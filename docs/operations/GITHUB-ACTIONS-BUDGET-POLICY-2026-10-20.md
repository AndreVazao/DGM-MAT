# GitHub Actions Budget Policy — 2026-10-20

## Goal
Preserve meaningful validation while avoiding repeated execution of the entire historical test matrix for every small change. Stability and evidence remain mandatory; Actions minutes are a constrained resource.

## Workflow policy
- `.github/workflows/backend-phase-gate.yml`: the seven-job full milestone gate is now manual-only (`workflow_dispatch`). Keep it for deliberate milestone audits, not routine PRs.
- `.github/workflows/targeted-pr-validation.yml`: routine PR validation compiles the source and runs only regression tests mapped to changed runtime files plus any changed test files. It is a single runner and cancels superseded runs for the same PR.
- Other build and broad validation workflows should remain manual unless there is a specific, current requirement for automatic execution.
- Do not rerun already-passing historical suites unless a relevant code path changed, a regression suggests it, or a milestone gate is explicitly requested.
- New functionality must add focused tests for its new contract; targeted CI should execute those changed tests.

## APK policy
- Repository `AndreVazao/DGM-MAT-Mobile` currently contains a lightweight web/PWA client, not a checked-in native Android project or APK build workflow.
- Do not claim an APK build passed until a real APK artifact exists and the build job is green.
- When a native APK workflow is introduced and its first intended build succeeds, disable that workflow immediately afterwards to prevent repeated Android SDK/Gradle minutes. Preserve the artifact/release link and workflow source; re-enable only for an explicitly requested new APK build.
- Before building the APK, verify the mobile client's configurable backend/rendezvous, authentication, and Android network security behavior; wrapping the current web client without those checks could produce an APK that builds but cannot connect to the PC brain.

## Evidence boundaries
GitHub Actions results are remote CI evidence only. They do not establish local PC runtime health or prove the user's machine can launch the generated package.
