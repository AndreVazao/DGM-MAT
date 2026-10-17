# DGM-MAT — Adaptive AI Engine and Agent Lifecycle

**Status:** target behaviour; runtime support must be verified before a feature is called operational.

## Selection order
1. Classify task complexity, privacy and resource needs.
2. Prefer deterministic code for simple work.
3. Inspect installed tools and models without starting heavy services.
4. Use local Ollama only when a suitable model is installed and measured resource thresholds allow it.
5. Use an approved free external agent when local capacity is insufficient and data-sharing policy allows it.
6. Never silently buy credits, subscribe or send private material to a provider.

## Lifecycle states
OFF → CHECKING → STARTING → READY → BUSY → STOPPING → OFF. Use DEGRADED/FAILED when probes fail or startup times out. Check process and port ownership before retrying to avoid duplicate servers. A process existing is not a health check; require a documented endpoint and bounded functional probe.

## Ollama
- Check the endpoint and model inventory first.
- Do not download models automatically on a resource-constrained PC.
- Start one managed instance only when a job needs it.
- Record whether DGM-MAT started the process or found it already running.
- Stop only a process DGM-MAT started and still owns, with no active dependent jobs.
- Never terminate all processes named Ollama indiscriminately.

## Claude Code Free and external agents
- Check installation and authentication state through supported diagnostics without printing credential files.
- Use task-specific working directories, bounded permissions and timeouts.
- External agents are helpers, not authorities over DGM-MAT policy.
- Do not allow agents to self-approve privileged commands, alter unrelated repositories, push/merge or change security settings.
- On quota errors, record sanitized details, wait or fall back to another allowed engine; do not purchase credits automatically.
- Never commit provider tokens or auth data.

## Resource-aware behaviour
Measure RAM, CPU and disk thresholds on the target PC and store them as configuration. On low-memory machines, serialize expensive jobs, use smaller models, avoid concurrent browser tabs/model loads, and defer heavy work rather than freezing the desktop.

## Dashboard telemetry
Show reachability, functional probe, selected model/provider, busy/idle state, last success, last check, degraded reason and whether the process is user-owned or DGM-managed. Green requires a successful functional probe; yellow means reachable but degraded/unverified; red means unreachable or unsupported.

## Required tests
- Already-running engine does not spawn duplicates.
- Stopped engine starts only when requested and allowed.
- Startup timeout produces a clear failure state.
- Active jobs prevent shutdown.
- User-owned processes are not terminated.
- Quota failures are redacted and trigger an allowed fallback.
- Low-memory conditions block heavy launches.
- Dashboard LEDs are based on live probes, not hardcoded labels.