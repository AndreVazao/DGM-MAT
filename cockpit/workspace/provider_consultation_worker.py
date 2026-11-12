"""Authenticated, free-only dispatch for explicit chat provider requests."""
from __future__ import annotations

from typing import Any

import requests
from PySide6.QtCore import QThread, Signal

from cockpit.api_client import authenticated_request, LocalApiAuthenticationError


_PROVIDER_LABELS = {
    "chatgpt": "ChatGPT",
    "grok": "Grok",
    "gemini": "Gemini",
    "claude": "Claude",
    "deepseek": "DeepSeek",
    "qwen": "Qwen",
}


class ProviderConsultationWorker(QThread):
    """Preview, enqueue and approve only the providers explicitly named in chat."""

    completed = Signal(str, str, str)

    def __init__(
        self,
        api_url: str,
        thread_id: str,
        goal: str,
        context: str,
        providers: tuple[str, ...],
    ) -> None:
        super().__init__()
        self.api_url = api_url.rstrip("/")
        self.thread_id = thread_id
        self.goal = goal.strip()
        self.context = context[:3500]
        self.providers = tuple(providers)
        self._approved_count = 0

    def _request(
        self, method: str, path: str, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        origin = self.api_url.rsplit("/runtime", 1)[0]
        if origin == self.api_url:
            raise ValueError("URL base do runtime não é válida para consultas browser.")
        response = authenticated_request(
            method,
            f"{origin}{path}",
            json=payload,
            timeout=(2, 12),
        )
        if response.status_code not in (200, 201):
            raise RuntimeError(
                f"Backend recusou a etapa {path.rsplit('/', 1)[-1]} "
                f"(HTTP {response.status_code})."
            )
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("O backend devolveu uma resposta de consulta inválida.")
        return data

    def _emit_status(self, message: str, kind: str = "system") -> None:
        self.completed.emit("Sistema" if kind == "system" else "Erro", message, kind)

    def run(self) -> None:
        labels = [_PROVIDER_LABELS.get(provider, provider) for provider in self.providers]
        provider_label = ", ".join(labels)
        try:
            if not self.thread_id or not self.goal or not self.providers:
                raise ValueError("Pedido de consulta incompleto; nada foi enviado.")

            status = self._request("GET", "/recovery/browser-consult/status")
            if status.get("enabled") is not True:
                self._emit_status(
                    "Não enviei a consulta a " + provider_label
                    + ": a consulta browser está desativada neste PC.",
                    "error",
                )
                return

            allowlisted = set(status.get("free_providers_allowlisted") or [])
            unavailable = [provider for provider in self.providers if provider not in allowlisted]
            if unavailable:
                missing = ", ".join(_PROVIDER_LABELS.get(item, item) for item in unavailable)
                self._emit_status(
                    "Não enviei a consulta: " + missing
                    + " não está configurado na allowlist gratuita deste PC. "
                    "Não usei outro provider nem qualquer fallback pago.",
                    "error",
                )
                return

            preview = self._request(
                "POST",
                "/recovery/browser-consult/preview",
                {"goal": self.goal, "context": self.context},
            )
            digest = preview.get("prompt_sha256")
            if not isinstance(digest, str) or len(digest) != 64:
                raise ValueError("O backend não devolveu um digest válido da pré-visualização.")

            queued = self._request(
                "POST",
                "/recovery/browser-consult/enqueue",
                {
                    "task_ref": "mobile-thread:" + self.thread_id,
                    "goal": self.goal,
                    "context": self.context,
                    "providers": list(self.providers),
                    # A local free-provider allowlist is the operator-configured capacity policy.
                    "free_capacity_confirmed": True,
                    "preview_sha256": digest,
                },
            )
            ids = queued.get("consultation_ids")
            if not isinstance(ids, list):
                ids = []
            ids = [item for item in ids if isinstance(item, str) and item]
            if not ids:
                self._emit_status(
                    "A consulta a " + provider_label
                    + " não foi colocada na fila. Estado: "
                    + str(queued.get("status") or "desconhecido")
                    + ". Não afirmei que algum provider foi contactado.",
                    "error",
                )
                return

            # The explicit natural-language command is this request's approval.
            # The same durable approval endpoint and audit path are still used.
            after_enqueue = self._request("GET", "/recovery/browser-consult/status")
            recent = after_enqueue.get("recent")
            recent = recent if isinstance(recent, list) else []
            states = {
                item.get("consultation_id"): item.get("status")
                for item in recent
                if isinstance(item, dict) and isinstance(item.get("consultation_id"), str)
            }
            approved = 0
            existing = 0
            for consultation_id in ids:
                current = states.get(consultation_id)
                if current in {"PENDING", "RUNNING", "COMPLETED"}:
                    existing += 1
                    continue
                self._request(
                    "POST",
                    "/recovery/browser-consult/approve/" + consultation_id,
                )
                approved += 1
                self._approved_count = approved

            if approved + existing != len(ids):
                raise RuntimeError("Nem todas as consultas ficaram aprovadas ou já estavam em curso.")
            redaction_note = (
                " O backend removeu conteúdo sensível da pré-visualização."
                if preview.get("prompt_redacted") is True else ""
            )
            if approved == 0 and existing:
                message = (
                    "Já existia uma consulta equivalente para " + provider_label
                    + "; não criei nem enviei uma duplicada."
                )
            else:
                message = (
                    "Pedido explícito reconhecido. "
                    + str(approved) + " consulta(s) aprovada(s) e colocada(s) na fila local para "
                    + provider_label + "."
                    + redaction_note
                    + " Ainda não afirmo que foram enviadas: a extensão Chrome tem de estar "
                    "emparelhada, com consultas ativadas e com os separadores dos providers disponíveis. "
                    "As respostas recebidas serão guardadas nesta conversa como propostas externas não verificadas."
                )
            self._emit_status(message)
        except LocalApiAuthenticationError:
            self._emit_status(
                "Não foi possível autenticar no backend local. Nenhuma consulta foi enviada.",
                "error",
            )
        except requests.Timeout:
            self._emit_status(
                "O pedido excedeu o tempo limite. O estado pode ser desconhecido; consulta a fila antes de repetir. "
                "Não voltei a enviar automaticamente.",
                "error",
            )
        except requests.RequestException:
            self._emit_status(
                "Não foi possível comunicar com o backend local. Nenhuma nova tentativa automática foi feita.",
                "error",
            )
        except (RuntimeError, ValueError, TypeError, KeyError) as exc:
            detail = str(exc)[:400] or "A consulta não foi concluída com segurança."
            if self._approved_count:
                detail = (
                    f"{self._approved_count} consulta(s) já ficaram aprovadas antes da falha. "
                    "Verifica o estado da fila antes de repetir. " + detail
                )
            self._emit_status(detail, "error")
