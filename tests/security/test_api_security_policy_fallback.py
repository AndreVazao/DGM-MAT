import pytest

from core.api.security_policy import SecurityScope, classify_request_path


@pytest.mark.parametrize(
    ("path", "method"),
    [
        ("/runtime/queue/actions/123/approve", "GET"),
        ("/runtime/queue/actions/123/reject", "GET"),
        ("/runtime/queue/actions/123/other", "POST"),
        ("/runtime/queue/actions//approve", "POST"),
        ("/runtime/queue/actions/123/approve/extra", "POST"),
    ],
)
def test_concrete_path_fallback_rejects_wrong_method_or_path(path, method):
    assert classify_request_path(path, method) is None


def test_concrete_path_fallback_keeps_operator_scope():
    result = classify_request_path("/runtime/queue/actions/123/approve", "POST")

    assert result is not None
    assert result.scope is SecurityScope.OPERATOR
