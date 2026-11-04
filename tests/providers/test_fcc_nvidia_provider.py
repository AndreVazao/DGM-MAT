from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import threading

import pytest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from core.providers.remote.fcc_nvidia_provider import FccNvidiaProvider, VERIFIED_FREE_MODELS
from core.provider_sync.provider_registry import ProviderRegistry, initialize_default_providers
from core.provider_sync.provider_request_policy import ProviderRequestPolicy
from core.provider_sync.governed_provider_service import GovernedProviderService
from core.governance.provider_rate_control import ProviderRateControl


class FakeFCC:
    def __init__(
        self, *, host="127.0.0.1", active_host=None, auth=True, model=None,
        opus_model=None, sonnet_model=None, haiku_model=None, provider_status="configured",
        redirect_models=False,
    ):
        self.host = host
        self.redirect_models = redirect_models
        self.active_host = active_host or host
        self.auth = auth
        self.model = model or next(iter(VERIFIED_FREE_MODELS))
        self.provider_status = provider_status
        self.opus_model = opus_model
        self.sonnet_model = sonnet_model
        self.haiku_model = haiku_model
        self.requests = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                return

            def _send(self, payload, status=200):
                body = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if self.path == "/admin/api/config":
                    fields = [
                        {"key": "HOST", "value": outer.host},
                        {"key": "MODEL", "value": outer.model},
                        {"key": "MODEL_OPUS", "value": outer.opus_model or ""},
                        {"key": "MODEL_SONNET", "value": outer.sonnet_model or ""},
                        {"key": "MODEL_HAIKU", "value": outer.haiku_model or ""},
                        {"key": "PORT", "value": str(outer.server.server_port)},
                    ]
                    self._send({"fields": fields})
                    return
                if self.path == "/admin/api/status":
                    self._send({
                        "status": "running",
                        "host": outer.active_host,
                        "port": outer.server.server_port,
                        "provider": "nvidia_nim",
                        "model": outer.model,
                        "provider_status": [{"provider_id": "nvidia_nim", "status": outer.provider_status}],
                    })
                    return
                if self.path == "/v1/models":
                    if outer.redirect_models:
                        self.send_response(302)
                        self.send_header("Location", "http://example.com/")
                        self.end_headers()
                        return
                    if outer.auth and self.headers.get("Authorization") != "Bearer " + outer.token:
                        self._send({"error": "unauthorized"}, 401)
                        return
                    self._send({"data": [
                        {"id": "anthropic/" + outer.model},
                        {"id": "claude-3-freecc-no-thinking/" + outer.model},
                    ]})
                    return
                self._send({"error": "not found"}, 404)

            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length)
                outer.requests.append({
                    "path": self.path,
                    "headers": dict(self.headers.items()),
                    "payload": json.loads(body.decode()),
                })
                if self.path != "/v1/messages":
                    self._send({"error": "not found"}, 404)
                    return
                if outer.auth and self.headers.get("Authorization") != "Bearer " + outer.token:
                    self._send({"error": "unauthorized"}, 401)
                    return
                self._send({"content": [{"type": "text", "text": "FCC_TEST_RESPONSE"}]})

        self.token = "test-token-that-is-long-enough-123456"
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def base_url(self):
        return f"http://127.0.0.1:{self.server.server_port}"

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_args):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


def make_provider(
    fake,
    tmp_path,
    *,
    daily_request_limit=2,
    daily_token_limit=8192,
    tokens_reserved_per_request=4096,
):
    provider = FccNvidiaProvider(
        base_url=fake.base_url,
        budget_db_path=tmp_path / "provider-budget.sqlite3",
        daily_request_limit=daily_request_limit,
        daily_token_limit=daily_token_limit,
        tokens_reserved_per_request=tokens_reserved_per_request,
        request_timeout_seconds=3,
        health_timeout_seconds=1,
    )
    provider.get_credential = lambda _kind: fake.token
    return provider


def test_provider_health_requires_loopback_auth_verified_model_and_nim_only_fallback(tmp_path):
    with FakeFCC() as fake:
        provider = make_provider(fake, tmp_path)
        health = provider.check_health()

    assert health["available"] is True
    assert health["model"] in VERIFIED_FREE_MODELS
    assert provider.is_available() is True
    assert provider.capabilities["cost_profile"] == "free"
    assert provider.config["billing_mode"] == "free_tier"
    assert provider.config["cost_verified"] is True


@pytest.mark.parametrize(
    ("kwargs", "expected_fragment"),
    [
        ({"host": "0.0.0.0"}, "loopback"),
        ({"active_host": "0.0.0.0"}, "active"),
        ({"auth": False}, "authentication"),
        ({"redirect_models": True}, "302"),
        ({"model": "nvidia_nim/nvidia/unknown-paid-model"}, "allowlist"),
        ({"opus_model": "openai/gpt-4.1"}, "tier routes"),
        ({"provider_status": "missing_key"}, "not configured"),
    ],
)
def test_provider_refuses_unsafe_or_unverified_fcc_configuration(tmp_path, kwargs, expected_fragment):
    with FakeFCC(**kwargs) as fake:
        provider = make_provider(fake, tmp_path)
        health = provider.check_health()

    assert health["available"] is False
    assert expected_fragment in health["reason"].lower()
    assert provider.is_available() is False
    assert provider.config["cost_verified"] is False
    assert provider.health_metrics["quota_limit"] is None


def test_provider_requires_strong_vault_credential(tmp_path):
    with FakeFCC() as fake:
        provider = make_provider(fake, tmp_path)
        provider.get_credential = lambda _kind: "weak"
        health = provider.check_health()

    assert health["available"] is False
    assert "strong" in health["reason"].lower()


def test_provider_atomically_reserves_daily_call_and_token_budget(tmp_path):
    with FakeFCC() as fake:
        provider = make_provider(fake, tmp_path)
        assert provider.check_health()["available"] is True
        assert provider.reserve_free_quota() is True
        assert provider.reserve_free_quota() is True
        assert provider.reserve_free_quota() is False

    assert provider.health_metrics["quota_used"] == 2


def test_provider_chat_uses_anthropic_messages_api_and_never_uses_tools(tmp_path):
    with FakeFCC() as fake:
        provider = make_provider(fake, tmp_path)
        assert provider.check_health()["available"] is True
        assert provider.reserve_free_quota() is True
        result = asyncio.run(provider.chat([
            {"role": "system", "content": "Return a concise patch only."},
            {"role": "user", "content": "Say FCC_TEST_RESPONSE"},
        ]))

    assert result == "FCC_TEST_RESPONSE"
    assert len(fake.requests) == 1
    request = fake.requests[0]
    assert request["path"] == "/v1/messages"
    assert request["headers"]["Authorization"] == "Bearer " + fake.token
    assert request["payload"]["model"] in VERIFIED_FREE_MODELS
    assert request["payload"]["system"] == "Return a concise patch only."
    assert request["payload"]["messages"] == [{"role": "user", "content": "Say FCC_TEST_RESPONSE"}]
    assert "tools" not in request["payload"]


def test_provider_registry_keeps_fcc_disabled_by_default(monkeypatch):
    registry = ProviderRegistry()
    monkeypatch.delenv("DGM_FCC_NVIDIA_ENABLED", raising=False)
    monkeypatch.setattr("core.provider_sync.provider_registry.provider_registry", registry)
    initialize_default_providers()
    assert registry.get_provider("nvidia_nim") is None


def test_provider_registry_requires_explicit_opt_in(monkeypatch):
    registry = ProviderRegistry()
    monkeypatch.setenv("DGM_FCC_NVIDIA_ENABLED", "1")
    monkeypatch.setattr("core.provider_sync.provider_registry.provider_registry", registry)
    initialize_default_providers()
    assert registry.get_provider("nvidia_nim") is not None


def test_governed_provider_service_calls_fcc_only_after_health_and_quota_preflight(tmp_path):
    with FakeFCC() as fake:
        provider = make_provider(fake, tmp_path)
        assert provider.check_health()["available"] is True
        registry = ProviderRegistry()
        registry.register(provider.name, provider)
        policy = ProviderRequestPolicy(registry, ProviderRateControl(5))
        service = GovernedProviderService(policy, timeout_seconds=5)

        result = asyncio.run(service.execute_chat(
            provider_id="nvidia_nim",
            request_id="fcc-request-001",
            messages=[{"role": "user", "content": "Say FCC_TEST_RESPONSE"}],
        ))

    assert result.success is True
    assert result.response == "FCC_TEST_RESPONSE"
    assert provider.health_metrics["quota_used"] == 1
    assert len(fake.requests) == 1


def test_provider_refuses_direct_chat_without_governed_quota_reservation(tmp_path):
    with FakeFCC() as fake:
        provider = make_provider(fake, tmp_path)
        assert provider.check_health()["available"] is True

        with pytest.raises(RuntimeError, match="quota policy"):
            asyncio.run(provider.chat([{"role": "user", "content": "Do not send this."}]))

    assert fake.requests == []


def test_provider_daily_budget_persists_across_provider_instances(tmp_path):
    with FakeFCC() as fake:
        first = make_provider(fake, tmp_path)
        assert first.check_health()["available"] is True
        assert first.reserve_free_quota() is True
        assert first.reserve_free_quota() is True

        second = make_provider(fake, tmp_path)
        health = second.check_health()

        assert health["quota_used"] == 2
        assert second.reserve_free_quota() is False


def test_provider_daily_budget_is_atomic_across_concurrent_instances(tmp_path):
    with FakeFCC() as fake:
        providers = [
            make_provider(
                fake,
                tmp_path,
                daily_request_limit=1,
                daily_token_limit=4096,
                tokens_reserved_per_request=4096,
            )
            for _ in range(2)
        ]
        assert all(provider.check_health()["available"] for provider in providers)

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda provider: provider.reserve_free_quota(), providers))

    assert sorted(results) == [False, True]


def test_provider_rejects_tool_and_provider_options_even_with_a_reserved_call(tmp_path):
    with FakeFCC() as fake:
        provider = make_provider(fake, tmp_path)
        with pytest.raises(ValueError, match="text messages only"):
            asyncio.run(provider.chat(
                [{"role": "user", "content": "No tools."}],
                tools=[{"name": "shell"}],
            ))

    assert fake.requests == []
