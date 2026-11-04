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
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
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


_HTTP_OPENER = build_opener(ProxyHandler({}), _NoRedirectHandler())


class FccProviderConfigurationError(RuntimeError):
    """FCC is not configured inside the provider's security boundary."""


class FccProviderHTTPError(RuntimeError):
    """HTTP failure retaining the status code for auth-boundary checks."""

    def __init__(self, status_code: int):
        self.status_code = status_code
        super().__init__(f"FCC returned HTTP {status_code}.")


class _RequestCancelled(RuntimeError):
    """Raised when a governed provider caller cancels its request."""


class FccNvidiaProvider(ProviderBase):
    """Free-tier NIM adapter through FCC's local Anthropic-compatible API."""

    requires_governed_request_id = True
    MAX_DAILY_REQUEST_LIMIT = 5
    MAX_DAILY_TOKEN_LIMIT = 25_000
    MAX_RESERVED_TOKENS_PER_REQUEST = 4_096
    MAX_OUTPUT_TOKENS = 2_048
    MAX_CONCURRENT_REQUESTS = 2
    ACTIVE_REQUEST_LEASE_SECONDS = 120.0

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
        if isinstance(daily_request_limit, bool) or not isinstance(daily_request_limit, int) or not 1 <= daily_request_limit <= self.MAX_DAILY_REQUEST_LIMIT:
            raise ValueError("daily_request_limit must be between 1 and 5")
        if isinstance(daily_token_limit, bool) or not isinstance(daily_token_limit, int) or not 1 <= daily_token_limit <= self.MAX_DAILY_TOKEN_LIMIT:
            raise ValueError("daily_token_limit must be between 1 and 25000")
        if isinstance(tokens_reserved_per_request, bool) or not isinstance(tokens_reserved_per_request, int) or not 1 <= tokens_reserved_per_request <= self.MAX_RESERVED_TOKENS_PER_REQUEST:
            raise ValueError("tokens_reserved_per_request must be between 1 and 4096")
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
            "max_output_tokens": self.MAX_OUTPUT_TOKENS,
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
        self._configured_caps = {
            "daily_request_limit": daily_request_limit,
            "daily_token_limit": daily_token_limit,
            "tokens_reserved_per_request": tokens_reserved_per_request,
            "max_output_tokens": self.MAX_OUTPUT_TOKENS,
            "request_timeout_seconds": float(request_timeout_seconds),
            "health_timeout_seconds": float(health_timeout_seconds),
        }

    def _validate_runtime_limits(self) -> None:
        """Reject persisted or runtime settings that exceed constructor-approved caps."""
        integer_limits = (
            "daily_request_limit", "daily_token_limit",
            "tokens_reserved_per_request", "max_output_tokens",
        )
        for key in integer_limits:
            value = self.config.get(key)
            cap = self._configured_caps[key]
            if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= cap:
                raise FccProviderConfigurationError(f"FCC setting {key} exceeds its validated constructor limit.")
        if self.config["tokens_reserved_per_request"] > self.config["daily_token_limit"]:
            raise FccProviderConfigurationError("Per-request token reservation exceeds the daily token budget.")
        for key, minimum in (("request_timeout_seconds", 1.0), ("health_timeout_seconds", 0.5)):
            value = self.config.get(key)
            cap = self._configured_caps[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not minimum <= value <= cap:
                raise FccProviderConfigurationError(f"FCC setting {key} exceeds its validated constructor limit.")
        model = self.config.get("model")
        if model is not None and model not in VERIFIED_FREE_MODELS:
            raise FccProviderConfigurationError("Persisted FCC model is outside the verified allowlist.")
        self._base_url()

    def validate_loaded_config(self) -> bool:
        """Validate saved values and discard persisted claims of live health or free billing."""
        self._validate_runtime_limits()
        self.config["model"] = None
        self.config["billing_mode"] = "unverified"
        self.config["cost_verified"] = False
        self.capabilities["cost_profile"] = "unknown"
        self.health_metrics["status"] = "unknown"
        self.health_metrics["last_check"] = 0
        self.health_metrics["quota_limit"] = None
        return True

    @staticmethod
    def _utc_day() -> str:
        """Return the canonical UTC date used by the persistent provider budget."""
        return datetime.now(timezone.utc).date().isoformat()

    @staticmethod
    def _ensure_request_active(cancel_event: threading.Event | None, deadline: float | None) -> None:
        """Fail before another FCC request when cancellation or the total deadline fires."""
        if cancel_event is not None and cancel_event.is_set():
            raise _RequestCancelled("FCC request was cancelled by its caller.")
        if deadline is not None and time.monotonic() >= deadline:
            raise TimeoutError("FCC request exceeded its total time budget.")

    @classmethod
    def _remaining_timeout(
        cls,
        configured_timeout: float,
        cancel_event: threading.Event | None,
        deadline: float | None,
    ) -> float:
        """Clamp each blocking operation to the remaining total request budget."""
        cls._ensure_request_active(cancel_event, deadline)
        if deadline is None:
            return float(configured_timeout)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("FCC request exceeded its total time budget.")
        return min(float(configured_timeout), remaining)

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
        cancel_event: threading.Event | None = None,
        deadline: float | None = None,
    ) -> dict[str, Any]:
        """Make one direct loopback request with redirect, size and deadline guards."""
        self._ensure_request_active(cancel_event, deadline)
        url = self._base_url() + path
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
            headers["x-api-key"] = token
            headers["anthropic-version"] = "2023-06-01"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(url, data=data, headers=headers, method="POST" if payload is not None else "GET")
        effective_timeout = self._remaining_timeout(
            timeout or float(self.config["request_timeout_seconds"]),
            cancel_event,
            deadline,
        )
        try:
            with _HTTP_OPENER.open(request, timeout=effective_timeout) as response:
                chunks: list[bytes] = []
                total = 0
                reader = getattr(response, "read1", response.read)
                while True:
                    read_timeout = self._remaining_timeout(effective_timeout, cancel_event, deadline)
                    response_file = getattr(response, "fp", None)
                    raw_stream = getattr(response_file, "raw", None)
                    sock = getattr(raw_stream, "_sock", None)
                    if sock is not None:
                        sock.settimeout(read_timeout)
                    chunk = reader(min(65_536, MAX_HTTP_RESPONSE_BYTES + 1 - total))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    total += len(chunk)
                    if total > MAX_HTTP_RESPONSE_BYTES:
                        raise ValueError("FCC response exceeds the configured byte limit.")
                raw = b"".join(chunks)
        except HTTPError as exc:
            self._ensure_request_active(cancel_event, deadline)
            raise FccProviderHTTPError(exc.code) from None
        except (_RequestCancelled, TimeoutError):
            raise
        except (URLError, OSError) as exc:
            raise RuntimeError(f"FCC request failed: {type(exc).__name__}") from None
        self._ensure_request_active(cancel_event, deadline)
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
        day = self._utc_day()
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

    def is_available(self) -> bool:
        """Refresh the UTC-day quota before the governed policy evaluates availability."""
        try:
            self._validate_runtime_limits()
            used_calls, _ = self._budget_snapshot()
        except (OSError, sqlite3.Error, ValueError, TypeError, RuntimeError):
            return False
        self.health_metrics["quota_used"] = used_calls
        return super().is_available()

    def check_health(
        self,
        *,
        cancel_event: threading.Event | None = None,
        deadline: float | None = None,
    ) -> dict[str, Any]:
        """Verify live FCC bind, auth, model and provider state within one total deadline."""
        now = time.time()
        self.health_metrics["last_check_attempt"] = now
        previous_state = {
            "status": self.health_metrics.get("status"),
            "last_check": self.health_metrics.get("last_check"),
            "quota_used": self.health_metrics.get("quota_used"),
            "quota_limit": self.health_metrics.get("quota_limit"),
            "error_count": self.health_metrics.get("error_count"),
            "billing_mode": self.config.get("billing_mode"),
            "cost_verified": self.config.get("cost_verified"),
            "cost_profile": self.capabilities.get("cost_profile"),
            "model": self.config.get("model"),
        }
        self.config["cost_verified"] = False
        self.config["billing_mode"] = "unverified"
        self.capabilities["cost_profile"] = "unknown"
        self.health_metrics["quota_limit"] = None
        try:
            self._validate_runtime_limits()
            self._ensure_request_active(cancel_event, deadline)
            health_timeout = float(self.config["health_timeout_seconds"])
            config_payload = self._request_json(
                "/admin/api/config", timeout=health_timeout,
                cancel_event=cancel_event, deadline=deadline,
            )
            status_payload = self._request_json(
                "/admin/api/status", timeout=health_timeout,
                cancel_event=cancel_event, deadline=deadline,
            )
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

            try:
                self._request_json(
                    "/v1/models", timeout=health_timeout,
                    cancel_event=cancel_event, deadline=deadline,
                )
            except FccProviderHTTPError as exc:
                if exc.status_code not in {401, 403}:
                    raise
            else:
                raise FccProviderConfigurationError(
                    "FCC proxy authentication failed: an unauthenticated model-discovery request was accepted."
                )
            model_payload = self._request_json(
                "/v1/models", token=token, timeout=health_timeout,
                cancel_event=cancel_event, deadline=deadline,
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

            self._ensure_request_active(cancel_event, deadline)
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
                "provider": self.name, "status": "ok", "available": True,
                "model": model, "billing_mode": "free_tier", "cost_verified": True,
                "quota_used": used_calls, "quota_limit": self.health_metrics["quota_limit"],
                "base_url": self.config["base_url"],
                "security": "loopback_and_proxy_auth_verified",
            }
        except (_RequestCancelled, TimeoutError):
            self.health_metrics.update({
                "status": previous_state["status"],
                "last_check": previous_state["last_check"],
                "quota_used": previous_state["quota_used"],
                "quota_limit": previous_state["quota_limit"],
                "error_count": previous_state["error_count"],
            })
            self.config.update({
                "billing_mode": previous_state["billing_mode"],
                "cost_verified": previous_state["cost_verified"],
                "model": previous_state["model"],
            })
            self.capabilities["cost_profile"] = previous_state["cost_profile"]
            raise
        except Exception as exc:
            self.health_metrics.update({
                "status": "unavailable", "last_check": now,
                "error_count": int(self.health_metrics.get("error_count", 0)) + 1,
                "quota_used": 0, "quota_limit": None,
            })
            return {
                "provider": self.name, "status": "unavailable", "available": False,
                "error": type(exc).__name__, "reason": str(exc)[:240],
                "base_url": self.config["base_url"],
            }

    def reserve_free_quota(self, request_id: str) -> bool:
        """Atomically reserve daily budget and one endpoint-wide request slot by request ID."""
        request_id = request_id.strip() if isinstance(request_id, str) else ""
        if not request_id or len(request_id) > 256:
            return False
        if self.health_metrics.get("status") != "ok" or self.config.get("cost_verified") is not True:
            return False
        try:
            self._validate_runtime_limits()
            daily_limit = int(self.config["daily_request_limit"])
            token_limit = int(self.config["daily_token_limit"])
            token_reserve = int(self.config["tokens_reserved_per_request"])
            day = self._utc_day()
            endpoint_key = self._base_url()
            lease_seconds = max(
                self.ACTIVE_REQUEST_LEASE_SECONDS,
                float(self.config["request_timeout_seconds"])
                + (4 * float(self.config["health_timeout_seconds"])) + 15.0,
            )
            self._budget_db_path.parent.mkdir(parents=True, exist_ok=True)
            with self._budget_lock, sqlite3.connect(
                self._budget_db_path, timeout=5, isolation_level=None
            ) as connection:
                connection.execute("PRAGMA busy_timeout=5000")
                connection.execute(
                    """CREATE TABLE IF NOT EXISTS provider_daily_budget (
                        provider_id TEXT NOT NULL, utc_day TEXT NOT NULL,
                        calls_used INTEGER NOT NULL DEFAULT 0,
                        tokens_reserved INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY (provider_id, utc_day)
                    )"""
                )
                connection.execute(
                    """CREATE TABLE IF NOT EXISTS provider_active_requests (
                        provider_id TEXT NOT NULL, endpoint_key TEXT NOT NULL,
                        request_id TEXT NOT NULL, utc_day TEXT NOT NULL,
                        lease_expires_at REAL NOT NULL,
                        PRIMARY KEY (provider_id, endpoint_key, request_id)
                    )"""
                )
                connection.execute("BEGIN IMMEDIATE")
                now = time.time()
                connection.execute(
                    "DELETE FROM provider_active_requests WHERE lease_expires_at <= ?",
                    (now,),
                )
                existing = connection.execute(
                    """SELECT 1 FROM provider_active_requests
                    WHERE provider_id=? AND endpoint_key=? AND request_id=?""",
                    (self.name, endpoint_key, request_id),
                ).fetchone()
                if existing:
                    connection.rollback()
                    return False
                active_count = connection.execute(
                    """SELECT COUNT(*) FROM provider_active_requests
                    WHERE provider_id=? AND endpoint_key=?""",
                    (self.name, endpoint_key),
                ).fetchone()[0]
                if int(active_count) >= self.MAX_CONCURRENT_REQUESTS:
                    connection.rollback()
                    return False

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
                    """INSERT INTO provider_daily_budget(provider_id, utc_day, calls_used, tokens_reserved)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(provider_id, utc_day)
                    DO UPDATE SET calls_used=excluded.calls_used, tokens_reserved=excluded.tokens_reserved""",
                    (self.name, day, calls_used + 1, tokens_reserved + token_reserve),
                )
                connection.execute(
                    """INSERT INTO provider_active_requests
                    (provider_id, endpoint_key, request_id, utc_day, lease_expires_at)
                    VALUES (?, ?, ?, ?, ?)""",
                    (self.name, endpoint_key, request_id, day, now + lease_seconds),
                )
                connection.commit()
                self.health_metrics["quota_used"] = calls_used + 1
                self.health_metrics["quota_limit"] = daily_limit
                return True
        except (OSError, sqlite3.Error, ValueError, TypeError, RuntimeError):
            return False

    def _active_request_day(self, request_id: str) -> str | None:
        """Return the unexpired UTC-day reservation for this exact governed request."""
        try:
            endpoint = self._base_url()
            with sqlite3.connect(self._budget_db_path, timeout=5) as connection:
                connection.execute("PRAGMA busy_timeout=5000")
                row = connection.execute(
                    """SELECT utc_day, lease_expires_at FROM provider_active_requests
                    WHERE provider_id=? AND endpoint_key=? AND request_id=?""",
                    (self.name, endpoint, request_id),
                ).fetchone()
                if row is None:
                    return None
                if float(row[1]) <= time.time():
                    connection.execute(
                        """DELETE FROM provider_active_requests
                        WHERE provider_id=? AND endpoint_key=? AND request_id=?""",
                        (self.name, endpoint, request_id),
                    )
                    connection.commit()
                    return None
                return str(row[0])
        except (OSError, sqlite3.Error, ValueError, TypeError, RuntimeError):
            return None

    def _release_active_request(self, request_id: str) -> None:
        """Release the shared endpoint slot after success, failure or cancellation."""
        try:
            with sqlite3.connect(self._budget_db_path, timeout=5) as connection:
                connection.execute("PRAGMA busy_timeout=5000")
                connection.execute(
                    """DELETE FROM provider_active_requests
                    WHERE provider_id=? AND endpoint_key=? AND request_id=?""",
                    (self.name, self._base_url(), request_id),
                )
                connection.commit()
        except (OSError, sqlite3.Error, ValueError, TypeError, RuntimeError):
            return

    def _chat_sync(
        self,
        messages: list[dict[str, str]],
        *,
        request_id: str,
        cancel_event: threading.Event,
    ) -> str:
        """Send one request only while its matching governed reservation remains valid."""
        deadline = time.monotonic() + float(self.config["request_timeout_seconds"])
        try:
            self._ensure_request_active(cancel_event, deadline)
            reserved_day = self._active_request_day(request_id)
            if reserved_day is None:
                raise RuntimeError("A matching governed request quota reservation is required.")
            if reserved_day != self._utc_day():
                raise RuntimeError("The governed quota reservation expired at UTC day rollover.")

            health = self.check_health(cancel_event=cancel_event, deadline=deadline)
            self._ensure_request_active(cancel_event, deadline)
            if health.get("available") is not True:
                raise RuntimeError("FCC provider is unavailable or its security configuration is unsafe.")
            if self._active_request_day(request_id) != self._utc_day():
                raise RuntimeError("The governed quota reservation expired before inference dispatch.")

            token = self.get_credential("api_key")
            if not isinstance(token, str) or len(token) < 24:
                raise RuntimeError("FCC proxy credential is unavailable.")
            if not isinstance(messages, list) or not messages or len(messages) > MAX_MESSAGES:
                raise ValueError("Messages must contain between 1 and 40 entries.")

            normalized: list[dict[str, str]] = []
            system_parts: list[str] = []
            total_chars = 0
            for message in messages:
                self._ensure_request_active(cancel_event, deadline)
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

            self._ensure_request_active(cancel_event, deadline)
            if self._active_request_day(request_id) != self._utc_day():
                raise RuntimeError("The governed quota reservation expired before inference dispatch.")
            response = self._request_json(
                "/v1/messages",
                payload=payload,
                token=token,
                timeout=float(self.config["request_timeout_seconds"]),
                cancel_event=cancel_event,
                deadline=deadline,
            )
            self._ensure_request_active(cancel_event, deadline)
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
        finally:
            self._release_active_request(request_id)

    async def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        """Execute FCC chat only for the request ID reserved by governed provider policy."""
        if set(kwargs) != {"request_id"}:
            raise ValueError("FCC chat requires only the governed request_id; direct or tool calls are refused.")
        request_id = kwargs.get("request_id")
        if not isinstance(request_id, str) or not request_id.strip() or len(request_id) > 256:
            raise ValueError("A valid governed request_id is required.")
        cancel_event = threading.Event()
        worker = asyncio.create_task(asyncio.to_thread(
            self._chat_sync,
            messages,
            request_id=request_id.strip(),
            cancel_event=cancel_event,
        ))
        try:
            return await asyncio.shield(worker)
        except asyncio.CancelledError:
            cancel_event.set()
            try:
                await asyncio.wait_for(asyncio.shield(worker), timeout=2.0)
            except (asyncio.TimeoutError, Exception):
                pass
            raise
