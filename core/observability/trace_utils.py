import os
from pathlib import Path

def trace_runtime_activation(message: str):
    """
    Prints a runtime activation trace message and appends it to .runtime/runtime_activation.log
    """
    print(message)
    trace_dir = Path(".runtime")
    try:
        trace_dir.mkdir(parents=True, exist_ok=True)
        log_file = trace_dir / "runtime_activation.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(message + "\n")
    except Exception:
        # Silently fail if we can't write to the log file to avoid breaking runtime
        pass
