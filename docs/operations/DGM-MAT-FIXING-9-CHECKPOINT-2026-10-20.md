# DGM-MAT Fixing 9 — Checkpoint 2026-10-20

## Completed and verified remotely

### Android APK — DGM-MAT-Mobile
- One-shot Android debug APK build: [GitHub Actions run 39409853967](https://github.com/AndreVazao/DGM-MAT-Mobile/actions/runs/39409853967).
- Result: client contract tests, Java setup, Android SDK package setup, Capacitor wrapper generation, Gradle debug build, and artifact upload all passed.
- Artifact: `DGM-MAT-Mobile-Android-APK`, artifact ID `12259215772`, size 3,698,457 bytes, SHA-256 `ee075ac10ddd967aeb57b053b2f1563e03453d1fffe0f98a4a83d0002e7b50be`.
- The workflow disabled itself after the successful upload to conserve Actions minutes. It is not meant to run automatically again.
- Boundary: packaging is verified; installing on a real Android device and validating reachability, pairing, authentication, and runtime API connectivity remain outstanding.

### Backend approval reconciliation
- PR [#130](https://github.com/AndreVazao/DGM-MAT/pull/130) merged as `4038a2bc250d8eadfafc50c09d5a298a1da1a9a5`.
- The legacy mission scheduler now reads the durable approval record as authoritative, persists a legacy decision to the approval queue before mutating the mission checkpoint, defers when a durable transition loses a race, and does not let stale `last_decision=reject` override a durable approval.
- Focused validation: [Focused PR Validation run 39415578897](https://github.com/AndreVazao/DGM-MAT/actions/runs/39415578897) passed; CodeRabbit and Snyk checks passed.
- This deliberately does not claim cross-store atomicity. Recovery depends on a later scheduler pass reconciling from the durable approval record.

### Digital office visual
- PR [#5](https://github.com/AndreVazao/DGM-Cockpit-Frontend/pull/5) merged as `5d875e3fe784778ade4938e05dfabda37bb3d9e9`.
- Added a responsive, accessible isometric SVG schematic inspired by the project's visual references.
- The drawing is explicitly static architecture, not live telemetry. Actual status remains in evidence-backed runtime cards; departments without a telemetry feed remain unknown.
- [Cockpit contract workflow run 39415774595](https://github.com/AndreVazao/DGM-Cockpit-Frontend/actions/runs/39415774595) passed.

## Actions minutes policy
- `.github/workflows/backend-phase-gate.yml` is manual-only for milestone audits.
- `.github/workflows/targeted-pr-validation.yml` handles routine relevant PR changes with a single runner, source compilation, and mapped regression tests only.
- Avoid rerunning already-passing historical suites unless the changed code path or a new failure justifies it.
- APK workflow remains disabled after its successful build. Re-enable only for an explicitly requested new build.

## Next engineering priorities
1. Continue stabilizing mission lifecycle/recovery and the durable queue; add only focused regressions for changed behavior.
2. Validate the APK on a physical Android device once available; do not infer runtime connectivity from build success.
3. Continue the PC cockpit and digital office incrementally, keeping chat primary and ensuring every live state has a real backend source.
4. Build the generic mission executor only after defining the result contract, allowed capability registry, approval boundary, timeout/cancellation behavior, and recovery semantics. Do not treat proposed subtasks as completed work.

## Evidence boundary
All CI results above are remote GitHub evidence. They do not prove that the user's PC has been tested or that the local runtime currently starts successfully.
