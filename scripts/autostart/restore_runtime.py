import json
from pathlib import Path

def restore():
    print("Restoring DGM-MAT Runtime State...")
    state_file = Path(".runtime/runtime_state.json")
    if state_file.exists():
        state = json.loads(state_file.read_text())
        print(f"Last status: {state.get('status')}")
    else:
        print("No runtime state found to restore.")

if __name__ == "__main__":
    restore()
