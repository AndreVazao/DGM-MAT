import pytest

def test_cockpit_import():
    try:
        from cockpit.app import run_cockpit
        assert run_cockpit is not None
        print("Successfully imported run_cockpit from cockpit.app")
    except ImportError as e:
        pytest.fail(f"Failed to import run_cockpit: {e}")

if __name__ == "__main__":
    test_cockpit_import()
