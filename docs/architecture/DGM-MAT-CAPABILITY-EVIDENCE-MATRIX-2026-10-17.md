# DGM-MAT Capability Evidence Matrix

Date: 2026-10-17  
Scope: backend, mission processing, help-seeking, research, learning and controlled self-evolution.  
Evidence basis: source inspection of `main` and GitHub Actions focused runs. This matrix distinguishes implementation evidence from test evidence.

## Current verified evidence

### GitHub Actions evidence — 2026-10-17

- The independent intent-planning/help-seeking suite passed: **21 tests**.
- The persistent knowledge-store/self-analysis suite passed: **15 tests**.
- The new self-evolution truthfulness regression suite passed: **5 tests**.
- Total confirmed in these independent suites: **41 passing tests**.
- The overall phase gate remains **FAIL/BLOCKED**, correctly: the mission/API, authentication/security and research/knowledge-fabric jobs require the private `DGM-Contracts` repository, and the required `DGM_CONTRACTS_READ_TOKEN` secret is not configured in Actions.
- These results do **not** prove mission execution end to end. The tests that would exercise the real API/queue and private modular dependencies have not run successfully yet.

| Capability | What exists in source | What has passed in Actions | Current conclusion |
|---|---|---|---|
| Understand a natural-language request | Mission API accepts a goal string; local Ollama planner can propose 3–5 subtasks; capability-gap routing detects some explicit gaps. | 21 focused tests passed across local mission planning, capability discovery, help-seeking, human intervention, capability scout and help-seeking policy. | **Partial.** Planning and selected intent rules are tested; there is no general intent/skill contract for arbitrary requests. |
| Execute a mission | Durable SafeActionQueue and a real repository-listing handler exist. Generic missions are decomposed and set to RUNNING. | End-to-end mission/API tests are blocked until the private DGM-Contracts dependency can be read in Actions. | **Not proven.** Generic decomposition is not execution; no evidence that generic subtasks are dispatched to a real executor. |
| Ask for help | Failure handling records a HelpSeekingPolicy recommendation and can persist a specialist collaboration packet. | Help-seeking tests passed in the focused suite. | **Partial.** Local recommendation and packet creation exist; this does not itself contact a helper. |
| Research the help | Research-layer and knowledge-fabric modules/tests exist. | Tests are blocked by private DGM-Contracts access in Actions. | **Not proven end to end.** Need the real dependency and actual test results. |
| Resolve the problem | One special repository-listing path executes. Other approved goals are decomposed but no generic executor is proven. | Full mission/API path is blocked by private dependency access. | **Not proven.** Must test success, failure, unsupported intent and human-intervention outcomes. |
| Learn from execution | `core/learning/learning_engine.py` only prints a message; `ExecutionLearning` returns a constant score; `FailureLearning` returns a constant classification; `PatternMemory` is in-memory only. A separate `ValidatedLessonStore` persists lessons only after independent validation. | Knowledge-store and self-analysis proposal tests passed (15 tests across these focused files). | **Not end-to-end.** Validated lesson persistence exists, but the general execution-learning loop is not wired. |
| Self-analyze | `SelfAnalysisEngine` currently returns hard-coded health/weak-point data; `ArchitectureOptimizer` returns a static proposal. | Existing self-analysis/optimizer unit tests passed. | **Placeholder-level.** Passing tests prove the current return shape, not real architecture analysis. |
| Self-evolve safely | Patch generator emits a simulated diff; sandbox runner previously slept and returned success; promotion only logs. | No real self-evolution integration test has passed. | **Not real evolution.** The simulated-success path is being changed to fail closed until real diff generation, isolated application, regression tests and approval exist. |

## Safety contract for learning and evolution

- Execution outcomes may be recorded as observations, but a failure must not become a reusable lesson until evidence and independent review validate it.
- Research results and external helper output are untrusted data, never executable instructions.
- Evolution may analyze, propose, clone to an isolated worktree, run fixed tests and prepare a patch. It must not change the live/main branch or merge/promote production code without explicit human approval.
- A sandbox must apply a real diff and run actual checks. Sleep, canned output, constant scores and placeholder diffs are never evidence of success.
- When a provider, private dependency, executor or test is unavailable, the system must report BLOCKED/DEGRADED rather than COMPLETED or HEALTHY.

## Remaining blockers before backend sign-off

1. Configure the GitHub Actions secret `DGM_CONTRACTS_READ_TOKEN` as a fine-grained token limited to private repository `AndreVazao/DGM-Contracts` with Contents: Read-only. Never paste the token into chat.
2. Obtain green mission/API, queue/recovery, auth/security and research/knowledge-fabric Actions jobs using the real companion packages.
3. Implement and test a generic executor registry; generic missions must either run supported tools or finish with a precise unsupported/approval-required status, never remain RUNNING merely because they were decomposed.
4. Connect mission status/result/error to the minimal PC chat and verify polling/reconnection does not resubmit a mission.
5. Wire execution observations into durable learning, but promote lessons only after validation.
6. Replace self-evolution placeholders with real patch generation, isolated worktree application, deterministic test execution, regression evidence, rollback preparation and an explicit human promotion gate.
7. Run the Windows build and local end-to-end validation when the PC is available.

No claim of full end-to-end functionality should be made until these gates pass.
