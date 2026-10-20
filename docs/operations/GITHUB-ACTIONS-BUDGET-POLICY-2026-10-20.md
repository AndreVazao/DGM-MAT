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

## Execution evidence — first Android APK (2026-10-20)

- Repository: `AndreVazao/DGM-MAT-Mobile`.
- Successful one-shot build: [GitHub Actions run 39409853967](https://github.com/AndreVazao/DGM-MAT-Mobile/actions/runs/39409853967).
- APK artifact: `DGM-MAT-Mobile-Android-APK`, 3,698,457 bytes (about 3.53 MiB), artifact ID `12259215772`.
- SHA-256: `ee075ac10ddd967aeb57b053b2f1563e03453d1fffe0f98a4a83d0002e7b50be`.
- Artifact retention expiry reported by GitHub: 2026-11-19 10:44 UTC.
- The job log confirms that the workflow disabled itself after successful APK build and artifact upload. Do not re-enable unless a new APK build is explicitly needed.
- Attempt 1 failed in Android SDK setup because the action tried to install the removed `tools` package. The workflow was corrected to use the runner's SDK manager directly; attempt 2 passed the client contract tests, SDK installation, Capacitor wrapper generation, Gradle debug build, artifact upload and workflow disable step.
- This is a debug APK. No Android-device installation or live PC pairing/authentication test has been claimed.

