# DGM-MAT unrestricted memory policy

**Decision:** DGM-MAT does not impose minimum or maximum RAM thresholds on task execution.

## Runtime behavior

- Hardware RAM size is still measured and exposed as diagnostic telemetry.
- The LOW_MEMORY profile name is informational; it no longer disables engines, defers provider/autonomy scans, or lazy-loads the knowledge engine.
- Local Ollama inference is not refused because available RAM falls below a configured threshold.
- Repository learning starts by default on all hardware profiles; `DGM_REPOSITORY_LEARNING_ENABLED=0` remains an explicit operator opt-out.
- Memory pressure does not trigger DGM-MAT cache pruning or memory-based task degradation/throttling.
- CPU safeguards, bounded command catalogs, approval gates, recursion protection, timeouts on individual external operations, and durable mission checkpoints remain in force. These are execution-safety controls, not RAM caps.

## Failure handling

DGM-MAT is allowed to run slowly while Windows manages memory pressure, including paging when configured by Windows. If Windows or a process terminates execution because resources are exhausted, DGM-MAT must record the actual failure, preserve the latest durable checkpoint, and avoid reporting completion or silently replaying a potentially mutating action.

No software policy can guarantee that Windows will remain responsive when physical and virtual memory are exhausted. The requirement is to avoid artificial DGM-MAT RAM gates, not to bypass operating-system resource protection.
