import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

try:
    print("Testing core.observability.trace_utils import...")
    from core.observability.trace_utils import trace_runtime_activation
    trace_runtime_activation("VALIDATION: trace_utils works")

    print("Testing main.py imports (without running main)...")
    import main
    print("main.py imported successfully")

    print("Testing scripts/autostart imports...")
    import scripts.autostart.start_runtime as sr
    import scripts.autostart.start_daemon as sd
    import scripts.autostart.start_dgm_mat as sdm
    print("Autostart scripts imported successfully")

    print("\nALL INSTRUMENTED FILES IMPORTABLE AND RUNNABLE FOR TRACING.")
except Exception as e:
    print(f"\nVALIDATION FAILED: {e}")
    sys.exit(1)
