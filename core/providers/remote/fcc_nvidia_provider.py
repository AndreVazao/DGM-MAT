"""Governed NVIDIA NIM access through a secured local Free Claude Code proxy."""
from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener
from typing import Any

from core.providers.base.provider_base import ProviderBase

VERIFIED_FREE_MODELS = frozenset({
    "nvidia_nim/nvidia/nemotron-3.5-super-vl-120b-a12b",
})
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
MAX_HTTP_RESPONSE_BYTES = 256_000
MAX_MESSAGES = 40
MAX_MESSAGE_CHARS = 12_000
MAX_TOTAL_INPUT_CHARS = 8_000
MAX_RESPONSE_CHARS = 16_000


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_HTTP_OPENER = build_opener(_NoRedirectHandler())


class FccProviderConfigurationError(RuntimeError):
    """FCC is not configured inside the provider's security boundary."""


class FccProviderHTTPError(RuntimeError):
    """HTTP failure retaining the status code for auth-boundary checks."""

    def __init__(self, status_code: int):
        self.status_code = status_code
        super().__init__(f"FCC returned HTTP {status_code}.")


class FccNvidiaProvider(ProviderBase):
    """Free-tier NIM adapter through FCC's local Anthropic-compatible API."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        budget_db_path: str | Path | None = None,
        daily_request_limit: int = 5,
        daily_token_limit: int = 25_000,
        tokens_reserved_per_request: int = 4_096,
        request_timeout_seconds: float = 30.0,
        health_timeout_seconds: float = 2.0,
    ) -> None:
        super().__init__("nvidia_nim")
        if isinstance(daily_request_limit, bool) or not isinstance(daily_request_limit, int) or daily_request_limit < 1:
            raise ValueError("daily_request_limit must be a positive integer")
        if isinstance(daily_token_limit, bool) or not isinstance(daily_token_limit, int) or daily_token_limit < 1:
            raise ValueError("daily_token_limit must be a positive integer")
        if isinstance(tokens_reserved_per_request, bool) or not isinstance(tokens_reserved_per_request, int) or tokens_reserved_per_request < 1:
            raise ValueError("tokens_reserved_per_request must be a positive integer")
        if tokens_reserved_per_request > daily_token_limit:
            raise ValueError("tokens_reserved_per_request cannot exceed daily_token_limit")
        if not 1 <= request_timeout_seconds <= 60 or not 0.5 <= health_timeout_seconds <= 10:
            raise ValueError("FCC request timeouts are outside the permitted range")

        self.config.update({
            "base_url": (base_url or os.getenv("DGM_FCC_BASE_URL", "http://127.0.0.1:8082")).rstrip("/"),
            "model": None,
            "billing_mode": "unverified",
            "cost_verified": False,
            "daily_request_limit": daily_request_limit,
            "daily_token_limit": daily_token_limit,
            "tokens_reserved_per_request": tokens_reserved_per_request,
            "max_output_tokens": 2_048,
            "request_timeout_seconds": float(request_timeout_seconds),
            "health_timeout_seconds": float(health_timeout_seconds),
            "cost_verification_date": "2026-11-04",
        })
        self.capabilities.update({
            "coding": 0.80,
            "reasoning": 0.85,
            "speed": 0.65,
            "context_size": 64_000,
            "cost_profile": "unknown",
        })
        self.health_metrics["quota_limit"] = daily_request_limit

        default_budget_path = Path(__file__).resolve().parents[3] / "storage" / "runtime" / "fcc_nvidia_budget.sqlite3"
        self._budget_db_path = Path(budget_db_path).expanduser().resolve() if budget_db_path else default_budget_path
        self._budget_lock = threading.RLock()
        self._pending_reservations = 0
        self._request_slots = threading.BoundedSemaphore(2)

    def _base_url(self) -> str:
        value = str(self.config.get("base_url", "")).rstrip("/")
        parsed = urlparse(value)
        if (
            parsed.scheme != "http"
            or parsed.hostname not in LOOPBACK_HOSTS
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or parsed.path not in {"", "/"}
        ):
            raise FccProviderConfigurationError("FCC endpoint must be a plain HTTP loopback URL.")
        return f"http://{parsed.netloc}"

    def _request_json(
        self,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        token: str | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        url = self._base_url() + path
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
            headers["x-api-key"] = token
            headers["anthropic-version"] = "2023-06-01"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(url, data=data, headers=headers, method="POST" if payload is not None else "GET")
        try:
            with _HTTP_OPENER.open(request, timeout=timeout or float(self.config["request_timeout_seconds"])) as response:
                raw = response.read(MAX_HTTP_RESPONSE_BYTES + 1)
        except HTTPError as exc:
            raise FccProviderHTTPError(exc.code) from None
        except (URLError, TimeoutError, OSError) as exc:
            raise RuntimeError(f"FCC request failed: {type(exc).__name__}") from None
        if len(raw) > MAX_HTTP_RESPONSE_BYTES:
            raise ValueError("FCC response exceeds the configured byte limit.")
        decoded = json.loads(raw.decode("utf-8"))
        if not isinstance(decoded, dict):
            raise ValueError("FCC returned a non-object JSON response.")
        return decoded

    @staticmethod
    def _field_map(config_payload: dict[str, Any]) -> dict[str, Any]:
        fields = config_payload.get("fields")
        if not isinstance(fields, list):
            raise FccProviderConfigurationError("FCC config response has no field list.")
        return {
            item.get("key"): item.get("value")
            for item in fields
            if isinstance(item, dict) and isinstance(item.get("key"), str)
        }

    def _budget_snapshot(self) -> tuple[int, int]:
        self._budget_db_path.parent.mkdir(parents=True, exist_ok=True)
        day = datetime.now(timezone.utc).date().isoformat()
        with sqlite3.connect(self._budget_db_path, timeout=5) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS provider_daily_budget (
                    provider_id TEXT NOT NULL,
                    utc_day TEXT NOT NULL,
                    calls_used INTEGER NOT NULL DEFAULT 0,
                    tokens_reserved INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (provider_id, utc_day)
                )
                """
            )
            row = connection.execute(
                "SELECT calls_used, tokens_reserved FROM provider_daily_budget WHERE provider_id=? AND utc_day=?",
                (self.name, day),
            ).fetchone()
        return (int(row[0]), int(row[1])) if row else (0, 0)

    def check_health(self) -> dict[str, Any]:
        now = time.time()
        self.health_metrics["last_check_attempt"] = now
        self.config["cost_verified"] = False
        self.config["billing_mode"] = "unverified"
        self.capabilities["cost_profile"] = "unknown"
        self.health_metrics["quota_limit"] = None
        try:
            self._base_url()
            config_payload = self._request_json("/admin/api/config", timeout=float(self.config["health_timeout_seconds"]))
            status_payload = self._request_json("/admin/api/status", timeout=float(self.config["health_timeout_seconds"]))
            fields = self._field_map(config_payload)

            host = fields.get("HOST")
            if not isinstance(host, str) or host.strip().casefold() not in LOOPBACK_HOSTS:
                raise FccProviderConfigurationError("FCC must bind to a loopback address (127.0.0.1/localhost/::1); 0.0.0.0 is refused.")
            token = self.get_credential("api_key")
            if not isinstance(token, str) or len(token) < 24:
                raise FccProviderConfigurationError("A strong FCC proxy token (24+ characters) must be stored in the DGM-MAT vault.")

            model = fields.get("MODEL")
            if not isinstance(model, str) or model not in VERIFIED_FREE_MODELS:
                raise FccProviderConfigurationError("FCC model is not in the verified free NVIDIA NIM allowlist.")
            routed_models = {
                key: fields.get(key)
                for key in ("MODEL_OPUS", "MODEL_SONNET", "MODEL_HAIKU")
                if isinstance(fields.get(key), str) and fields.get(key).strip()
            }
            if any(value not in VERIFIED_FREE_MODELS for value in routed_models.values()):
                raise FccProviderConfigurationError("Paid or unverified Claude tier routes are prohibited.")

            if status_payload.get("status") != "running":
                raise FccProviderConfigurationError("FCC server is not running.")
            active_host = status_payload.get("host")
            if not isinstance(active_host, str) or active_host.strip().casefold() not in LOOPBACK_HOSTS:
                raise FccProviderConfigurationError("Active FCC server process is not bound to loopback.")
            active_port = status_payload.get("port")
            configured_port = urlparse(self._base_url()).port or 80
            try:
                manifest_port = int(fields.get("PORT"))
            except (TypeError, ValueError):
                raise FccProviderConfigurationError("FCC configured port is missing or invalid.") from None
            if (
                isinstance(active_port, bool)
                or not isinstance(active_port, int)
                or active_port != configured_port
                or manifest_port != configured_port
            ):
                raise FccProviderConfigurationError("FCC configured/active port does not match the DGM-MAT loopback endpoint.")
            if status_payload.get("provider") != "nvidia_nim" or status_payload.get("model") != model:
                raise FccProviderConfigurationError("FCC active provider/model does not match the verified NIM configuration.")
            provider_states = status_payload.get("provider_status")
            nim_state = next(
                (
                    item for item in provider_states
                    if isinstance(item, dict) and item.get("provider_id") == "nvidia_nim"
                ),
                None,
            ) if isinstance(provider_states, list) else None
            if not isinstance(nim_state, dict) or nim_state.get("status") != "configured":
                raise FccProviderConfigurationError("NVIDIA NIM API key is not configured in FCC.")

            # Prove auth is enforced: without a token /v1/models must reject us.
            # Then prove the vault token is accepted. Neither request runs inference.
            try:
                unauthenticated = self._request_json(
                    "/v1/models",
                    timeout=float(self.config["health_timeout_seconds"]),
                )
            except FccProviderHTTPError as exc:
                if exc.status_code not in {401, 403}:
                    raise
            else:
                if isinstance(unauthenticated.get("data"), list):
                    raise FccProviderConfigurationError("FCC proxy authentication is disabled.")
                raise FccProviderConfigurationError("Unauthenticated FCC model discovery did not return an authorization error.")

            model_payload = self._request_json(
                "/v1/models",
                token=token,
                timeout=float(self.config["health_timeout_seconds"]),
            )
            model_entries = model_payload.get("data")
            advertised_ids = {
                item.get("id") for item in model_entries if isinstance(item, dict)
            } if isinstance(model_entries, list) else set()
            expected_gateway_ids = {
                f"anthropic/{model}",
                f"claude-3-freecc-no-thinking/{model}",
            }
            if not advertised_ids.intersection(expected_gateway_ids):
                raise FccProviderConfigurationError("Authenticated FCC model discovery did not expose the verified NIM model.")

            used_calls, _ = self._budget_snapshot()
            self.config.update({
                "model": model,
                "billing_mode": "free_tier",
                "cost_verified": True,
            })
            self.capabilities["cost_profile"] = "free"
            self.health_metrics.update({
                "status": "ok",
                "last_check": now,
                "error_count": 0,
                "quota_used": used_calls,
                "quota_limit": int(self.config["daily_request_limit"]),
            })
            return {
                "provider": self.name,
                "status": "ok",
                "available": True,
                "model": model,
                "billing_mode": "free_tier",
                "cost_verified": True,
                "quota_used": used_calls,
                "quota_limit": self.health_metrics["quota_limit"],
                "base_url": self.config["base_url"],
                "security": "loopback_and_proxy_auth_verified",
            }
        except Exception as exc:
            self.health_metrics.update({
                "status": "unavailable",
                "last_check": now,
                "error_count": int(self.health_metrics.get("error_count", 0)) + 1,
                "quota_used": 0,
                "quota_limit": None,
            })
            return {
                "provider": self.name,
                "status": "unavailable",
                "available": False,
                "error": type(exc).__name__,
                "reason": str(exc)[:240],
                "base_url": self.config["base_url"],
            }

    def reserve_free_quota(self) -> bool:
        """Atomically reserve one request and a conservative token allowance per UTC day."""
        if self.health_metrics.get("status") != "ok" or self.config.get("cost_verified") is not True:
            return False
        daily_limit = int(self.config["daily_request_limit"])
        token_limit = int(self.config["daily_token_limit"])
        token_reserve = int(self.config["tokens_reserved_per_request"])
        day = datetime.now(timezone.utc).date().isoformat()
        self._budget_db_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with self._budget_lock, sqlite3.connect(self._budget_db_path, timeout=5, isolation_level=None) as connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS provider_daily_budget (
                        provider_id TEXT NOT NULL,
                        utc_day TEXT NOT NULL,
                        calls_used INTEGER NOT NULL DEFAULT 0,
                        tokens_reserved INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY (provider_id, utc_day)
                    )
                    """
                )
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    "SELECT calls_used, tokens_reserved FROM provider_daily_budget WHERE provider_id=? AND utc_day=?",
                    (self.name, day),
                ).fetchone()
                calls_used, tokens_reserved = (int(row[0]), int(row[1])) if row else (0, 0)
                if calls_used >= daily_limit or tokens_reserved + token_reserve > token_limit:
                    connection.rollback()
                    self.health_metrics["quota_used"] = calls_used
                    return False
                connection.execute(
                    """
                    INSERT INTO provider_daily_budget(provider_id, utc_day, calls_used, tokens_reserved)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(provider_id, utc_day)
                    DO UPDATE SET calls_used=excluded.calls_used, tokens_reserved=excluded.tokens_reserved
                    """,
                    (self.name, day, calls_used + 1, tokens_reserved + token_reserve),
                )
                connection.commit()
                self.health_metrics["quota_used"] = calls_used + 1
                self._pending_reservations += 1
                return True
        except (OSError, sqlite3.Error, ValueError, TypeError):
            return False

    def _chat_sync(self, messages: list[dict[str, str]]) -> str:
        # Re-check the live proxy before every inference so a changed bind/auth/
        # fallback configuration cannot be used from a stale health snapshot.
        health = self.check_health()
        if health.get("available") is not True:
            raise RuntimeError("FCC provider is unavailable or its security configuration is unsafe.")
        with self._budget_lock:
            if self._pending_reservations < 1:
                raise RuntimeError("FCC inference must pass the governed provider quota policy first.")
            self._pending_reservations -= 1
        token = self.get_credential("api_key")
        if not isinstance(token, str) or len(token) < 24:
            raise RuntimeError("FCC proxy credential is unavailable.")

        if not isinstance(messages, list) or not messages or len(messages) > MAX_MESSAGES:
            raise ValueError("Messages must contain between 1 and 40 entries.")
        normalized: list[dict[str, str]] = []
        system_parts: list[str] = []
        total_chars = 0
        for message in messages:
            if not isinstance(message, dict) or set(message) != {"role", "content"}:
                raise ValueError("Malformed provider message.")
            role, content = message.get("role"), message.get("content")
            if role not in {"system", "user", "assistant"} or not isinstance(content, str) or not content.strip():
                raise ValueError("Unsupported provider message.")
            if len(content) > MAX_MESSAGE_CHARS:
                raise ValueError("Provider message exceeds the per-message limit.")
            total_chars += len(content)
            if total_chars > MAX_TOTAL_INPUT_CHARS:
                raise ValueError("Provider request exceeds the total input limit.")
            if role == "system":
                system_parts.append(content.strip())
            else:
                normalized.append({"role": role, "content": content.strip()})
        if not normalized:
            raise ValueError("At least one user or assistant message is required.")

        payload: dict[str, Any] = {
            "model": self.config["model"],
            "max_tokens": int(self.config["max_output_tokens"]),
            "messages": normalized,
            "temperature": 0.1,
        }
        if system_parts:
            payload["system"] = "\n\n".join(system_parts)

        if not self._request_slots.acquire(timeout=1):
            raise RuntimeError("FCC local concurrency limit reached.")
        try:
            response = self._request_json(
                "/v1/messages",
                payload=payload,
                token=token,
                timeout=float(self.config["request_timeout_seconds"]),
            )
        finally:
            self._request_slots.release()

        content = response.get("content")
        if not isinstance(content, list):
            raise ValueError("FCC response has no content blocks.")
        text_parts = [
            item.get("text")
            for item in content
            if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str)
        ]
        result = "\n".join(text_parts).strip()
        if not result or len(result) > MAX_RESPONSE_CHARS:
            raise ValueError("FCC response is empty or exceeds the text limit.")
        return result

    async def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        if kwargs:
            raise ValueError("FCC provider accepts text messages only; provider options and tools are not supported.")
        return await asyncio.to_thread(self._chat_sync, messages)
