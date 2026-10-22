# Programming & Software Engineering Department — Readiness Audit and Technical Contract

**Date:** 2026-10-22  
**Status:** evidence-based design and partial implementation; not a claim of runtime readiness  
**Branch:** `audit/programming-department-readiness-2026-10-22`  
**Repository:** `AndreVazao/DGM-MAT`

## Executive finding

The canonical operating model already defines Programming & Software Engineering, independent QA/Bug Hunting, Research, DevOps, Security/Governance, Data/Memory/Docs, Providers, Product/Cockpit and Hardware/Device Integration. It also names the initial language specialties. The gap is not a missing department name: the next requirement is to connect that design to real task contracts, toolchain detection, safe execution, independent validation and evidence-backed results.

A source review found concrete placeholders in the default branch:

- `core/development/code_generation.py`: `CodeGenerationEngine.generate_code()` unconditionally returns an empty list.
- `core/autonomous_dev/dead_code_detector.py`: `DeadCodeDetector.find_dead_code()` unconditionally returns an empty list.
- `core/development/development_models.py` provides basic `CodeChange`, `FeaturePlan`, `SpecializedAgent` and `ValidationResult` models, but these alone do not implement code generation, language-specific validation or a secure patch-application lifecycle.
- `core/development/validation_engine.py`: `validate_implementation()` returns `ValidationResult(success=True)` unconditionally, with no checks.
- `core/development/architecture_validator.py`: references `Any` without importing it and currently always builds an empty error list; the import/runtime failure was inferred from source, not executed here.
- `core/development/implementation_engine.py`: backs up a local `.env` file if present, logs a message and returns `IN_PROGRESS`; it does not apply generated changes. The automatic environment backup also needs a path/retention/secret-handling review before this engine is reused.
- `core/development/development_engine.py` and `core/development/execution_fabric.py`: the visible implementation dispatches into an in-memory list and returns a feature ID; it does not demonstrate a durable worker lifecycle or completed implementation.
- `core/development/feature_planner.py`: derives IDs from Python's process-randomized built-in `hash()`, so IDs are not stable across processes/runs.
- `docs/DGM-MAT_DIGITAL_ORGANIZATION_BUILD_ORDER.md` explicitly places runtime integration, governance, worker lifecycle and the pilot departments ahead of expanding the agent fleet.

These are confirmed source-level observations from the files inspected. Search results did not reveal production callers for the named stubs beyond the legacy/optional development path, but repository-wide caller discovery is not exhaustive. The findings mean this development subsystem must not be treated as a reliable implementation/validation pipeline. Do not wire it into production, remove it, or replace its interfaces until callers/imports and compatibility needs are mapped and tests exist. The unstable IDs and unconditional validation success are explicit blockers.

## Department contract

### Responsibilities

1. Clarify requirements and acceptance criteria without changing the user's intent.
2. Inspect the target repository, branch, current state, dependencies, callers and tests before editing.
3. Route tasks to a demonstrated language/toolchain capability, not merely an agent name or prompt.
4. Produce minimal, reviewable diffs with explicit affected paths and rationale.
5. Validate syntax, imports/types, lint/static analysis, unit/integration/API/UI tests, security and packaging according to project risk and available tooling.
6. Ask independent QA/Bug Hunting to reproduce and challenge the result; the author cannot be the only approver of a critical change.
7. Preserve a recoverable checkpoint, record exact commit/file hashes and test outputs, and update the project documentation/memory.
8. Report `verified`, `implemented_not_tested`, `partial`, `blocked`, or `not_implemented` truthfully.

### Explicit non-responsibilities

- The programming department does not grant itself permissions, approve its own critical architecture changes, or bypass the CEO/owner governance gates.
- A plan, generated patch, successful HTTP response, empty error list, or installed compiler does not prove that a change works.
- Model-generated code is untrusted input. Never execute it before policy checks, path validation, review and an appropriate isolated test boundary.
- A filename extension is a useful hint, not definitive language identification; project manifests and neighboring files may resolve ambiguity.
- Do not create a separate worker for every language on the weak PC. Use a small number of logical roles and dispatch only when the capability is needed.

## Language and specialization matrix

| Priority | Specialty | Required responsibilities | Validation gates |
|---|---|---|---|
| P0 | Python | Backend, APIs, automation, agents and tests | Parse/compile, imports, lint/type checks when configured, unit/integration/API, security |
| P0 | JavaScript / TypeScript | Cockpit logic, Node services, client contracts | Syntax/typecheck, lint, unit, build, browser/API integration |
| P0 | HTML / CSS | Semantics, responsive UI, accessibility | HTML/CSS validation, accessibility, viewport/browser checks |
| P0 | SQL / data | Schema, queries, migration, persistence | Dialect-aware validation, migration review, integrity/rollback, query plans |
| P0 | PowerShell / Windows | PC install, diagnostics, services, packaging | Parse/static checks, safe dry-run, Windows integration, privilege review |
| P0 | Shell / Bash | Linux/CI automation | Syntax, shell static analysis when installed, dry-run, integration |
| P1 | Java / Kotlin / Android | APK/mobile clients and Android integration | Compile, static checks, unit, emulator/device integration, package signing checks |
| P1 | Git / CI and configuration | Versioning, YAML/JSON/TOML, workflows | Diff/branch integrity, schema/format checks, secret scan, manual Actions policy |
| Conditional | C/C++, Rust, Go, C#/.NET and others | Only when a real repository/workload requires them | Toolchain-specific compile, static analysis, tests and packaging |

HTML is markup and CSS is a stylesheet language; both still need dedicated expertise, but should not be mislabeled as general-purpose programming languages. YAML/JSON/TOML are configuration formats, not programming languages. A `.h` file is ambiguous between C and C++ without project context.

## Partial implementation in this branch

Added `core/development/language_catalog.py`, a deterministic, standard-library-only catalogue that:

- distinguishes programming languages, markup, stylesheets, shell, SQL, configuration and ambiguous headers;
- maps common source/configuration extensions to canonical profiles;
- provides language-specific *recommended* validation stages;
- labels all toolchains as `requires_environment_probe`;
- keeps `execution_enabled=False` and returns a `plan_only` result, never claiming tools were detected or tests executed;
- fails closed for unknown extensions with `blocked_unknown_language`.

This is a routing/metadata primitive, not a code-generation engine, compiler detector, linter runner or proof of language execution support. It is deliberately safe to integrate later behind the existing programming/organization contracts.

Also added `core/development/toolchain_probe.py`, an explicit, allowlisted version-probe utility for common interpreters, compilers and developer tools. It accepts only fixed tool IDs and fixed argument lists, never uses a shell, clamps the timeout to 0.2–5 seconds, distinguishes unavailable/timeout/failed/available, and does not install packages or execute project source. Probing occurs only when explicitly called; catalogue presence is not an availability assertion.

Three unsafe legacy development behaviors were also corrected on this branch:
- `ValidationEngine.validate_implementation()` now fails closed with an explicit error until real validation adapters run; it no longer returns success unconditionally.
- `ArchitectureValidator` imports `Any` correctly and refuses to certify empty or unchecked changes until structural rules exist.
- `FeaturePlanner` now derives IDs from a stable SHA-256 digest and rejects empty requests, instead of using process-randomized `hash()`.

These are intentionally conservative safety gates, not a claim that implementation or architecture validation is complete. The legacy implementation engine, execution fabric and dead-code detector still require a caller/contract audit before they can be safely integrated.

## Required architecture before calling the department operational

### Intake and plan
Every programming task must include mission/task ID, source request, repository + branch + base SHA, permitted paths, target language, expected output, acceptance criteria, risk/reversibility, dependencies and timeout/resource budget. Missing repository context or an ambiguous destructive change blocks mutation.

### Toolchain and execution
Use a capability probe that records executable/version/path/exit code/time and whether the tool was actually invoked. Separate detection from execution. Use argument arrays (not shell string concatenation), bounded stdout/stderr, timeouts, allowed working directories and explicit environment. Never execute arbitrary source from an imported conversation.

### Patch lifecycle
`inspect → plan → snapshot → patch → diff-review → syntax/type/static checks → tests → independent QA → acceptance decision → commit/merge gate`.

A failed check blocks promotion. A test that was unavailable is `not_run`, not `passed`. A generated patch is a proposal until applied and validated. No destructive cleanup without caller/history checks and a recoverable checkpoint.

### Multi-language routing
A language catalogue maps to capabilities; the capability registry must separately report `available / unavailable / degraded / not_probed`, tool versions and environment constraints. Mixed-language work becomes linked subtasks with explicit contracts; the integration lead checks API/schema compatibility. A file extension alone never grants an executor.

### Independent QA
QA receives the task intent, diff, base SHA, test evidence and acceptance criteria. It checks regressions, security, imports/callers, persistence, error paths, path portability, Windows compatibility, licensing and the exact output. QA can reject the delivery and request a bounded repair loop; the author cannot silently mark its own work verified.

### Reliability and memory
Persist plans, task transitions, diffs, tool invocations, test output summaries, artifacts and final evidence. Redact secrets and avoid storing entire sensitive environment dumps. Record lessons only after verified outcomes. Update the canonical roadmap and AndreOS-Memory checkpoint at meaningful milestones.

## Implementation sequence

1. **Catalogue (this branch):** language metadata and planning-only validation profiles.
2. **Tests (this branch):** pure unit tests for extension resolution, ambiguity, unknown languages, and fail-closed planning semantics.
3. **Repository/toolchain inventory:** enumerate manifests, lockfiles, compilers/interpreters, linters, test frameworks and existing CI/manual-build constraints. Do not infer installed tools from dependencies alone.
4. **Programming task contract:** align language selection and patch metadata with the existing mission/organization/task models; avoid creating a competing mission state store.
5. **Safe toolchain probes:** read-only, bounded probes; no installation or network download without explicit policy.
6. **Validation adapters:** small adapters for installed tools; structured result schema and timeout/output limits.
7. **Patch application:** isolated working tree or branch, explicit allowed paths, snapshot/rollback and diff review.
8. **Independent QA gates:** focused regression suite and negative tests; preserve the one-open-PR policy.
9. **Runtime integration:** connect to actual worker lifecycle, durable missions, Event Bus and cockpit only after their contracts are verified.
10. **PC verification:** run tests/builds on André's Windows PC; capture exact command, commit SHA, output, resource impact and recovery behavior.

## Test status and release gate

Nineteen unit tests (7 language-catalogue + 6 toolchain-probe + 6 development safety-gate tests) were executed against isolated temporary copies of the modules and test files: **19 passed**. This was not a checkout of the full repository and does not replace running the tests on the actual branch/Windows PC. No compiler/linter availability is claimed, and no runtime/build test was run. The branch is intentionally separate from the existing governance PR #143; no second PR has been opened.

Before merge: run the new tests; run focused development/organization tests; verify imports/callers and Python compatibility; test unknown/ambiguous extensions; verify no code execution occurs; then update the roadmap with results. Before declaring the Programming department operational, prove at least one supported language end-to-end from task intake through safe patch, real validation, independent QA, durable result and truthful final report.

## Canonical references

- `docs/architecture/DGM-MAT-CANONICAL-OPERATING-MODEL-END-TO-END-AND-DEPARTMENTS-2026-10-21.md`
- `docs/DGM-MAT_DIGITAL_ORGANIZATION_BUILD_ORDER.md`
- `docs/architecture/DGM-MAT-MASTER-BRAIN-FIRST-IMPLEMENTATION-ROADMAP-2026-10-22.md`
- `docs/operations/AGENT_SHELL_GIT_POLICY.md`

The roadmap remains authoritative for overall sequencing. This audit supplements it and does not claim the full repository or all language specialists are already implemented.


## Follow-up contract/caller audit — 2026-10-22

### Caller-search result and its limits

Targeted repository searches for `DevelopmentEngine.process_request`, `ImplementationEngine.execute_implementation`, `CodeGenerationEngine.generate_code`, `DeadCodeDetector.find_dead_code` and `ValidationEngine.validate_implementation` returned the class/method definitions and the legacy `DevelopmentEngine` internal call chain, but did not establish a broader production call graph. Search-index results are not a substitute for a local repository-wide AST/import scan. Before changing or deleting public interfaces, run a local scan across Python imports, dynamic imports, dependency injection, tests, entry points and configuration.

The visible legacy call chain is:

`process_request → FeaturePlanner.plan_feature → ExecutionFabric.dispatch (in-memory append) → ImplementationEngine.execute_implementation → DevelopmentMemory.record_feature → return feature_id`.

This path does **not** call `ValidationEngine.validate_implementation`, does not call `CodeGenerationEngine.generate_code`, does not apply a patch and does not wait for a worker. `ImplementationEngine.execute_implementation` invokes its `.env` backup side effect before returning `IN_PROGRESS`. Consequently, even though the method returns an identifier and records a status, that is not evidence that source code was changed or validated. Avoid using this path as a live coding endpoint until its contract is replaced or adapted with tests and an explicit migration plan.

### Safe integration decision

- Do not wire the planning-only language catalogue to the legacy implementation path yet.
- Do not invoke `execute_implementation` merely to obtain a status; its `.env` backup side effect is unrelated to actual implementation and may copy secrets into the working directory.
- Do not treat an empty result from code generation or dead-code detection as proof that no changes or dead code exist.
- Preserve legacy modules while mapping callers and writing compatibility tests. No deletion or broad refactor is justified by the current evidence.
- The next engineering increment should define one explicit result contract shared by planning, patch proposal, execution, validation and durable task state. It must distinguish `planned`, `blocked`, `not_implemented`, `running`, `failed`, and `verified`; only a real configured validator may produce `verified`.
- Before any source mutation, require repository root/base SHA, allowed paths, a recoverable checkpoint and a diff review. Do not back up `.env` into a plain local file by default; secrets need explicit exclusion/redaction and a controlled backup policy.

### Evidence and open gates

Confirmed from inspected source: the methods and behaviors listed above. Not yet confirmed: complete repository-wide caller graph, runtime importability of every legacy module, full test suite, Windows compatibility, toolchain availability on André's PC, and end-to-end patch execution. No PR has been opened for this audit branch; PR #143 remains the sole open PR and remains blocked on its separate security/test gates.


## Shared task-result contract — 2026-10-22

Added `core/development/task_result.py` and focused tests in `tests/test_development_task_result.py` on this audit branch. The standard-library contract distinguishes `planned`, `blocked`, `not_implemented`, `running`, `failed`, and `verified`. It does not execute work or persist state; it provides a consistent truthful result shape for future integration.

The contract rejects empty task IDs/summaries, malformed full commit hashes, success flags on non-verified states, and `verified` unless both validation and independent QA are explicitly passed with evidence references. This is a local contract primitive, not yet wired to Mission Engine, Execution Fabric, API routes, durable task storage, or the cockpit. Its new tests have been added but have **not yet been executed**. Existing isolated 19-test result remains separate evidence and does not include these new tests.
