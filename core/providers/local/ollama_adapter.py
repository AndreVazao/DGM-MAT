"""Local-only Ollama adapter; never calls paid or remote model APIs."""
from __future__ import annotations
import asyncio
import json
import os
import time
from typing import Any
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from core.providers.base.provider_base import ProviderBase


class OllamaProvider(ProviderBase):
    """Small-model inference through a loopback-only Ollama HTTP endpoint."""

    def __init__(self):
        super().__init__("ollama")
        self.config.update({
            "base_url": os.getenv("DGM_OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/"),
            "model": os.getenv("DGM_OLLAMA_MODEL", "llama3.2:1b"),
            "coder_model": os.getenv("DGM_OLLAMA_CODER_MODEL", os.getenv("DGM_OLLAMA_MODEL", "llama3.2:1b")),
            "num_ctx": 512,
            "num_predict": 256,
            "health_timeout_seconds": 1.5,
            "request_timeout_seconds": 90.0,
            "keep_alive": 0,
        })
        self._installed_models: list[str] = []
        self.capabilities.update({
            "coding": 0.55,
            "reasoning": 0.45,
            "speed": 0.55,
            "context_size": 1024,
            "cost_profile": "local_zero_token",
        })

    def _base_url(self) -> str:
        value = str(self.config.get("base_url", "")).rstrip("/")
        parsed = urlparse(value)
        if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("Ollama adapter is loopback-only; remote model endpoints are not allowed")
        if parsed.port not in {None, 11434}:
            raise ValueError("Ollama adapter only permits the local default port 11434")
        return value

    def _request_json(self, path: str, payload: dict | None = None, *, timeout: float | None = None) -> dict[str, Any]:
        url = self._base_url() + path
        headers = {"Content-Type": "application/json"}
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(url, data=data, headers=headers, method="POST" if payload is not None else "GET")
        with urlopen(request, timeout=timeout or float(self.config["request_timeout_seconds"])) as response:
            result = json.loads(response.read().decode("utf-8"))
        if not isinstance(result, dict):
            raise ValueError("Ollama returned a non-object JSON response")
        return result

    def check_health(self) -> dict[str, Any]:
        now = time.time()
        self.health_metrics["last_check_attempt"] = now
        started = time.monotonic()
        try:
            payload = self._request_json("/api/tags", timeout=float(self.config["health_timeout_seconds"]))
            models = payload.get("models", [])
            self._installed_models = sorted({
                item["name"] for item in models
                if isinstance(item, dict) and isinstance(item.get("name"), str) and item["name"].strip()
            })
            available = bool(self._installed_models)
            self.health_metrics["status"] = "ok" if available else "unavailable"
            self.health_metrics["last_check"] = now
            if available:
                self.health_metrics["error_count"] = 0
        except (OSError, URLError, TimeoutError, ValueError, TypeError) as exc:
            self._installed_models = []
            self.health_metrics["status"] = "unavailable"
            self.health_metrics["last_check"] = now
            self.health_metrics["error_count"] += 1
            return {
                "provider": self.name,
                "status": "unavailable",
                "available": False,
                "models": [],
                "error": type(exc).__name__,
                "base_url": self.config["base_url"],
            }
        latency_ms = (time.monotonic() - started) * 1000
        self.record_latency(latency_ms)
        return {
            "provider": self.name,
            "status": self.health_metrics["status"],
            "available": bool(self._installed_models),
            "models": list(self._installed_models),
            "latency_ms": round(latency_ms, 2),
            "base_url": self.config["base_url"],
            "cost_profile": "local_zero_token",
        }

    @staticmethod
    def available_memory_gb() -> float | None:
        try:
            import psutil
            return psutil.virtual_memory().available / (1024 ** 3)
        except Exception:
            return None

    def generate(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        json_mode: bool = False,
        num_ctx: int | None = None,
        num_predict: int | None = None,
    ) -> str:
        available_gb = self.available_memory_gb()
        minimum_gb = max(0.5, float(os.getenv("DGM_OLLAMA_MIN_FREE_GB", "1.25")))
        allow_low_memory = os.getenv("DGM_OLLAMA_ALLOW_LOW_MEMORY", "0").strip().casefold() in {"1", "true", "yes", "on"}
        if available_gb is not None and available_gb < minimum_gb and not allow_low_memory:
            raise RuntimeError(
                f"Local inference skipped to protect the PC: {available_gb:.2f} GB RAM available; "
                f"{minimum_gb:.2f} GB required. No remote provider fallback is attempted."
            )
        if not isinstance(messages, list) or not messages or len(messages) > 40:
            raise ValueError("messages must contain between 1 and 40 items")
        normalized = []
        for item in messages:
            if not isinstance(item, dict) or item.get("role") not in {"system", "user", "assistant"}:
                raise ValueError("each message must have a supported role and content")
            content = item.get("content")
            if not isinstance(content, str) or not content.strip() or len(content) > 12000:
                raise ValueError("message content must be non-empty and at most 12000 characters")
            normalized.append({"role": item["role"], "content": content.strip()})

        if not self._installed_models or time.time() - float(self.health_metrics.get("last_check", 0)) > 30:
            health = self.check_health()
            if not health.get("available"):
                raise RuntimeError("Local Ollama is unavailable; deterministic fallback must be used")
        selected = model or str(self.config["model"])
        if selected not in self._installed_models:
            raise ValueError(f"Requested local model is not installed: {selected}")
        context_size = max(512, min(int(num_ctx or self.config["num_ctx"]), 2048))
        output_tokens = max(1, min(int(num_predict or self.config["num_predict"]), 512))
        payload: dict[str, Any] = {
            "model": selected,
            "messages": normalized,
            "stream": False,
            "options": {"num_ctx": context_size, "num_predict": output_tokens, "temperature": 0.2},
            "keep_alive": self.config.get("keep_alive", 0),
        }
        if json_mode:
            payload["format"] = "json"
        started = time.monotonic()
        response = self._request_json("/api/chat", payload)
        message = response.get("message", {})
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Ollama returned no message content")
        self.record_latency((time.monotonic() - started) * 1000)
        self.health_metrics["status"] = "ok"
        self.health_metrics["last_check"] = time.time()
        return content.strip()

    async def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        return await asyncio.to_thread(self.generate, messages, **kwargs)
