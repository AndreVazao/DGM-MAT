from pathlib import Path

from scripts.validate_executable import _redacted_tail


def test_redacted_tail_removes_bearer_and_secret_values(tmp_path: Path):
    log = tmp_path / "child.log"
    log.write_text(
        "Authorization: Bearer abc123\ntoken=secret-value\napi_key: another-secret\n",
        encoding="utf-8",
    )

    result = _redacted_tail(log)

    assert "abc123" not in result
    assert "secret-value" not in result
    assert "another-secret" not in result
    assert result.count("[REDACTED]") == 3


def test_redacted_tail_is_bounded(tmp_path: Path):
    log = tmp_path / "child.log"
    log.write_text("\n".join(f"line-{index}" for index in range(10)), encoding="utf-8")

    result = _redacted_tail(log, max_lines=3)

    assert result.splitlines() == ["line-7", "line-8", "line-9"]
