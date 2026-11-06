# Adaptive Runtime Capability and Shared AI Agents
<!-- Path: C:\ProgramasGodMode\DGM-MAT\docs\architecture\ADAPTIVE_RUNTIME_CAPABILITY_AND_SHARED_AGENTS_2026-10-11.md -->

Date: 2026-10-11
Status: partial implementation. A read-only host capability profile and API route are implemented and locally tested; automatic model routing and shared-agent execution remain inactive.

## Decision

DGM-MAT must adapt to the machine it is running on, not encode the current PC as a permanent capacity limit. The present Windows PC is a constrained deployment profile. A future i7-class host with 32-64 GB RAM must be able to use the same system with a different live capability profile, without rewriting project policy or mission logic.

The same AI worker may serve DGM-MAT, VazaoSovereignTrader, Baribudos Studio and other explicitly registered projects. Shared worker availability does not imply shared project data, permissions, credentials, or write access.

## Runtime capability profile

Discover at startup and refresh conservatively at safe checkpoints:

- OS, CPU logical cores, total/available RAM, process memory, GPU/VRAM if reliably detectable;
- local inference endpoints and models actually available (Ollama, LM Studio, llama.cpp);
- provider readiness, current quota/rate-limit evidence, request timeout and observed latency;
- task class, context size, required tools, data sensitivity, deadline and allowed side effects.

Separate detected facts from estimates. Unknown hardware/provider capability must not be represented as available capacity. Profile collection is observational and must not load every model or launch heavy benchmarks.

## Model/agent routing policy

1. Use deterministic code or cached evidence where adequate; do not call a model needlessly.
2. Prefer a small local model for lightweight classification, extraction, summarization and first-pass triage when the live resource budget says it is safe.
3. Use a more capable local model for deeper local reasoning when available capacity and measured latency support it.
4. Use the shared Claude Code Free agent for bounded code investigation, tests and engineering assistance when its CLI/provider path has passed a health check and the project explicitly delegates the task.
5. Use NVIDIA NIM for deeper or difficult work when its provider is ready and the task policy allows remote processing. Free access must never be assumed unlimited: observe documented/account quotas, 429/rate-limit responses, timeouts and cost/usage signals where exposed.
6. Before any paid path, require explicit human approval, a known cost/limit and operation within that limit. No silent paid fallback.
7. On quota exhaustion or timeout, use a cheaper approved alternative, wait if appropriate, or return BLOCKED/PARTIAL with evidence. Bound retries and never fan out indefinitely.

Routing is based on task requirements and live evidence, not a hard-coded assumption that the current machine always has low memory or that NIM is always free/available.

## Resource adaptation

- Resource limits are runtime budgets, not product limitations. Keep configurable profiles such as `constrained`, `balanced` and `high_capacity`, but select them from observed capabilities and explicit operator overrides.
- Preserve a safety reserve for Windows and the DGM-MAT core. If free memory falls below the configured reserve, defer or reject optional local inference rather than destabilize the host.
- On a stronger host, automatically raise concurrency/context/model eligibility only after detecting capacity and validating provider readiness; retain bounded concurrency and cancellation.
- Avoid parallel heavy inference/build/test tasks on constrained hosts. On high-capacity hosts, concurrency may rise within configured ceilings.
- Recompute after host changes/reinstall; do not migrate machine-specific RAM thresholds into permanent business rules.

## Shared worker contract

Each delegated task must include project ID, repository/workspace root, goal, acceptance criteria, verified facts, unknowns, relevant prior evidence, permitted operations, timeout/budget and correlation ID. Return result, evidence, changed paths, tests and unresolved risks.

Project isolation rules:

- Worker access is restricted to the requesting project's explicitly authorized roots for that task.
- Memory retrieval is project-scoped by default; cross-project lessons may be shared only as generalized knowledge without leaking project secrets or private artefacts.
- No commits, pushes, destructive actions, credential handling, paid spend, or external side effects without the relevant explicit authorization and gate.
- A shared agent is a worker, not the global authority: DGM-MAT remains the coordinator and policy enforcement point.

## Current verified state and blockers (2026-10-11)

- DGM-MAT health endpoint returned `healthy` on port 8181; runtime process remained stable in the latest observed checks.
- Local Ollama API responded with version `0.23.0`; its provider is marked configured in the Free Claude Code provider inventory. The exact locally installed model list should be enumerated before assigning a specific model by name.
- Free Claude Code dashboard and FCC server are running; NVIDIA NIM is marked configured/ready and the default selected model is Nemotron 3 Super 120B, with a lighter Nemotron 3.5 Lightning 30B alias. This status is not proof of unlimited quota or successful end-to-end completion.
- A previous minimal chat test did not return a clean, verified answer. The CLI also produced a `bash.exe.stackdump` showing failures in `msys-2.0.dll`. Git for Windows Bash exists at `C:\Program Files\Git\bin\bash.exe`; passing this path explicitly to the dashboard's child process is a candidate fix, not yet applied or verified.
- The dashboard's `server.js` could not be overwritten in-place during the attempted safe edit because Windows reported the file was in use. A byte-for-byte backup was created as `server.js.bak-20261011-gitbash`; the original was not changed by that failed write.
- FCC admin status reports `0.0.0.0:8082`. Exposure beyond loopback has not been verified; treat it as a security finding until listener/firewall/access scope is established. Do not blindly rewrite configuration or firewall rules.
- Provider registration in DGM-MAT remains safe-off. The governed provider execution API currently supports bounded chat with durable approval; it does not confer tool, browser, shell, or file-write capability. The FCC agent must not be wired as a general autonomous executor until a narrow adapter, approval policy, cancellation, redaction, project scoping and integration tests exist.

## Next implementation gates

1. Verify the actual FCC CLI path, Bash selection, process exit code and minimal text response with tools disabled; keep the test bounded and record logs without secrets.
2. Resolve and test the Bash crash; validate the dashboard SSE `result`/`exit` events and ensure timeouts terminate only the current child process.
3. Determine whether the FCC admin listener is reachable from other interfaces; restrict it to loopback through the supported configuration if exposure is confirmed and after preserving the current config.
4. Implement a read-only capability profile with unit tests for missing/unknown hardware and provider data.
5. Add a deterministic routing decision module with mocked providers: lightweight local, deeper local, FCC coding worker, NIM, wait/fallback, and blocked/no-spend paths.
6. Add a project-scoped FCC adapter behind the existing governed provider boundary; keep tool execution and writes disabled until separately approved and tested.
7. Test that quota exhaustion, 429, timeout, missing credentials, low RAM, cancellation and unapproved paid paths never cause silent spending or unbounded retries.
8. Validate on this constrained PC without heavy benchmarks, then validate again on the stronger host. Do not encode this PC's limits as global constants.

## Validation principle

No feature is considered operational merely because an endpoint returns HTTP 200 or a provider is marked configured. Require an end-to-end result, exit status, evidence, resource impact and regression tests before declaring success.


## Implementation checkpoint — 2026-10-11 07:58 Portugal

Implemented:
- `core/governance/runtime_capability_profile.py`: cheap, read-only OS/CPU/RAM/process-RSS observations; adaptive `unknown`, `constrained`, `balanced`, and `high_capacity` tiers; a host-scaled memory safety reserve; optional-inference eligibility; bounded optional concurrency; explicit unknown-data warnings.
- `GET /governance/runtime-capabilities` in `core/api/governance_api.py`, returning a JSON-safe profile.
- `tests/unit/test_runtime_capability_profile.py`: tests for small/large hosts, unknown observations, low available memory, JSON serialization, live collection, and the route.

Validation on the current host: 8 tests passed across the new profile tests and existing resource-monitor lifecycle tests; Python compilation and `git diff --check` passed. The live read-only observation saw 2 logical CPU cores, about 2.96 GiB total RAM, and about 0.98 GiB available at the observation time; optional inference was correctly marked unavailable because free RAM was at/below the safety reserve. This is a transient host observation, not a permanent product limit.

The API process was not restarted, so the new route is in source but is not yet loaded by the running process. No commit or push was made.

Separate Vercel finding: `core/api/api_server.py` starts a rendezvous heartbeat every 60 seconds, and `core/federation/rendezvous_client.py` sends a POST to `https://dgm-mat-rendezvous.vercel.app/api/rendezvous`. At continuous uptime this is about 1,440 registration attempts/day before any other traffic. This is a strong candidate for the 2,000-request alert, but actual billable usage has not been verified. Do not change heartbeat cadence or Vercel settings as part of this step; preserve phone/PC discovery until the user chooses a quota fix.


## 2026-10-11 — Vercel rendezvous pausado até ativação do telemóvel

Decisão do utilizador: como o telemóvel ainda não está instalado/configurado e a quota Free do Vercel foi excedida, pausar a descoberta rendezvous até o sistema PC/telemóvel estar pronto para entrar em operação.

Implementação em `core/api/api_server.py`:
- `DGM_RENDEZVOUS_ENABLED` tem por defeito o valor desligado. O heartbeat só arranca se a variável estiver explicitamente definida como `1/true/yes/on`.
- Quando for reativado, o intervalo por defeito passa a 20 minutos (1200 s), configurável por `DGM_RENDEZVOUS_INTERVAL_SECONDS` e limitado entre 60 s e 24 h.
- Não foram feitas alterações no projeto Vercel nem no endpoint remoto.
- Backup anterior à alteração: `core/api/api_server.py.bak-rendezvous-pause-20261011`.

Aplicação: o Core foi reiniciado de forma controlada para carregar a nova política. O PID anterior 3480 foi substituído pelo PID 7096. Health voltou a HTTP 200 em `127.0.0.1:8181`; o listener continua apenas em loopback. Não existiam overrides de ambiente User/Machine para as duas variáveis no momento da verificação, pelo que o heartbeat fica desativado no processo atual e em arranques normais futuros, até ativação explícita.

Testes: `tests/unit/test_rendezvous_heartbeat_policy.py` cobre default desativado, ativação explícita e intervalo de 20 minutos/limites; em conjunto com os testes do perfil adaptativo e lifecycle do resource monitor, 14 testes passaram. Compilação Python e `git diff --check` passaram. A nova rota de capacidades devolveu 403 sem sessão, consistente com a política de autenticação global; não foi testada com uma sessão autorizada.

Nota de quota: 60 s representavam ~1.440 tentativas de registo por dia de uptime contínuo; o novo intervalo de 20 minutos representará ~72 tentativas/dia quando reativado. Isto não prova o consumo faturável exato do Vercel. A quota excedida não é reposta por esta alteração; a ação apenas impede novas chamadas originadas por este heartbeat no runtime reiniciado.

Reativar apenas quando o utilizador autorizar a entrada em operação PC/telemóvel; definir explicitamente `DGM_RENDEZVOUS_ENABLED=1` e confirmar a quota/uso do Vercel antes. Não commitar nem publicar sem autorização.
