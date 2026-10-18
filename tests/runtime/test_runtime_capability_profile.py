from core.governance.runtime_capability_profile import collect_runtime_capability_profile


def test_runtime_capability_profile_is_json_serializable_and_read_only():
    profile = collect_runtime_capability_profile()
    data = profile.to_dict()

    assert data["operating_system"]
    assert data["operating_system_release"]
    assert data["architecture"]
    assert data["python_version"]
    assert data["logical_cpu_count"] >= 1
    assert data["memory_total_bytes"] is None or data["memory_total_bytes"] > 0
    assert data["memory_available_bytes"] is None or data["memory_available_bytes"] >= 0
    assert isinstance(data["ollama_available"], bool)
    assert isinstance(data["claude_code_available"], bool)
    assert data["capability_source"] == "python-standard-library"
    assert data["profile_kind"] == "observed-host-snapshot"
