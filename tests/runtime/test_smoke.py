import subprocess
import sys
import os

def test_runtime_smoke_success():
    """Verify that the runtime smoke test passes."""
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    result = subprocess.run(
        [sys.executable, "scripts/runtime_smoke_test.py"],
        env=env,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "SMOKE TEST: PASSED" in result.stdout
