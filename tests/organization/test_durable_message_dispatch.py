"""Regression tests for durable organization messages and explicit worker dispatch."""
from core.organization.message_bus import InternalMessageBus
from core.organization.models import Message, MessagePriority
from core.organization.worker_runtime import WorkerRuntime


def test_durable_bus_survives_new_instance_and_persists_read_state(tmp_path):
    database = tmp_path / "organization_messages.sqlite3"
    original = Message(
        sender_id="agent:hq-orchestrator",
        recipient_id="agent:bug-hunter",
        subject="Independent review required",
        body="Review the stored result; do not trust it automatically.",
        mission_id="mission:test",
        priority=MessagePriority.HIGH,
        requires_response=True,
        correlation_id="collab:test",
    )
    first = InternalMessageBus(database)
    first.send(original)
    first.close()

    second = InternalMessageBus(database)
    received = second.receive("agent:bug-hunter", unread_only=True)
    assert len(received) == 1
    assert received[0].message_id == original.message_id
    assert received[0].priority is MessagePriority.HIGH
    assert received[0].correlation_id == "collab:test"
    assert received[0].mission_id == "mission:test"

    second.mark_read("agent:bug-hunter", original.message_id)
    second.close()

    third = InternalMessageBus(database)
    assert third.receive("agent:bug-hunter", unread_only=True) == []
    assert len(third.receive("agent:bug-hunter")) == 1
    third.close()


def test_durable_bus_does_not_overwrite_existing_message_on_duplicate_id(tmp_path):
    database = tmp_path / "messages.sqlite3"
    first = InternalMessageBus(database)
    message = Message("agent:a", "agent:b", "subject", "original", message_id="stable-id")
    first.send(message)
    first.mark_read("agent:b", "stable-id")
    first.send(message)
    assert first.receive("agent:b")[0].body == "original"
    assert first.receive("agent:b", unread_only=True) == []
    first.close()


def test_worker_runtime_executes_only_registered_handler_and_acknowledges_success(tmp_path):
    bus = InternalMessageBus(tmp_path / "messages.sqlite3")
    message = Message("agent:hq", "agent:bug-hunter", "Review", "untrusted content")
    bus.send(message)
    runtime = WorkerRuntime(bus)
    seen = []
    runtime.register_handler("agent:bug-hunter", lambda item: seen.append(item.message_id) or {"review": "received"})

    result = runtime.dispatch_one("agent:bug-hunter")

    assert result is not None
    assert result.status == "HANDLED"
    assert result.result == {"review": "received"}
    assert seen == [message.message_id]
    assert bus.receive("agent:bug-hunter", unread_only=True) == []
    bus.close()


def test_worker_runtime_leaves_message_unread_when_handler_fails(tmp_path):
    bus = InternalMessageBus(tmp_path / "messages.sqlite3")
    message = Message("agent:hq", "agent:bug-hunter", "Review", "untrusted content")
    bus.send(message)
    runtime = WorkerRuntime(bus)

    def fail(_message):
        raise RuntimeError("expected test failure")

    runtime.register_handler("agent:bug-hunter", fail)
    result = runtime.dispatch_one("agent:bug-hunter")

    assert result is not None
    assert result.status == "HANDLER_FAILED_UNACKNOWLEDGED"
    assert result.error_type == "RuntimeError"
    assert [item.message_id for item in bus.receive("agent:bug-hunter", unread_only=True)] == [message.message_id]
    bus.close()


def test_worker_runtime_refuses_unregistered_agent_handler(tmp_path):
    bus = InternalMessageBus(tmp_path / "messages.sqlite3")
    runtime = WorkerRuntime(bus)
    try:
        runtime.dispatch_one("agent:not-registered")
    except KeyError as exc:
        assert "No explicit worker handler" in str(exc)
    else:
        raise AssertionError("Dispatch without a registered handler must fail closed.")
    bus.close()
