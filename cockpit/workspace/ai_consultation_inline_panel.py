"""Compact in-chat panel for explicit, free-tier browser AI consultations."""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from cockpit.workspace.ai_consultation_dialog import _ConsultationWorker


class AIConsultationInlinePanel(QFrame):
    """A small provider picker embedded in the active conversation."""

    status_message = Signal(str)

    PROVIDERS = (
        ("chatgpt", "ChatGPT"),
        ("grok", "Grok"),
        ("gemini", "Gemini"),
        ("claude", "Claude"),
        ("deepseek", "DeepSeek"),
        ("qwen", "Qwen"),
    )

    def __init__(self, api_url: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.api_url = api_url
        self.thread_id: str | None = None
        self._worker: _ConsultationWorker | None = None
        self._status_loaded = False
        self._consult_enabled = False
        self._allowed_providers: set[str] = set()
        self._approval_ids: list[str] = []
        self._approved_count = 0
        self._approval_total = 0
        self._continue_approval = False
        self._setup_ui()
        self.hide()

    def _setup_ui(self) -> None:
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            "QFrame { background: #202328; border: 1px solid #3e4652; border-radius: 7px; }"
            "QLabel { color: #d8dee9; border: none; }"
            "QLineEdit { background: #17191d; color: #f3f4f6; border: 1px solid #505866; padding: 6px; border-radius: 4px; }"
            "QCheckBox { color: #e5e7eb; border: none; }"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(9, 7, 9, 7)
        layout.setSpacing(5)

        top = QHBoxLayout()
        top.addWidget(QLabel("Consultar uma ou mais IAs — transporte browser gratuito"))
        top.addStretch(1)
        self.close_button = QPushButton("Fechar")
        self.close_button.setMaximumWidth(64)
        self.close_button.clicked.connect(self.hide)
        top.addWidget(self.close_button)
        layout.addLayout(top)

        self.goal = QLineEdit()
        self.goal.setMaxLength(4000)
        self.goal.setPlaceholderText("Pergunta para as IAs (por omissão, a última mensagem desta conversa)")
        self.goal.textChanged.connect(self._refresh_controls)
        layout.addWidget(self.goal)

        providers = QHBoxLayout()
        self.provider_checks: dict[str, QCheckBox] = {}
        for provider, label in self.PROVIDERS:
            check = QCheckBox(label)
            check.setChecked(provider == "chatgpt")
            check.toggled.connect(self._refresh_controls)
            self.provider_checks[provider] = check
            providers.addWidget(check)
        providers.addStretch(1)
        layout.addLayout(providers)

        actions = QHBoxLayout()
        self.status = QLabel("A verificar providers permitidos neste PC…")
        self.status.setWordWrap(True)
        actions.addWidget(self.status, 1)
        self.send_button = QPushButton("Pedir consulta")
        self.send_button.clicked.connect(self._enqueue)
        actions.addWidget(self.send_button)
        layout.addLayout(actions)

    def set_thread_context(self, thread_id: str | None, latest_user_message: str = "") -> None:
        self.thread_id = thread_id
        if latest_user_message.strip():
            self.goal.setText(latest_user_message.strip()[:4000])
        self._refresh_controls()

    def refresh_status(self) -> None:
        self._status_loaded = False
        self._start_request("status", "GET", "/recovery/browser-consult/status")

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._status_loaded and self._worker is None:
            self.refresh_status()

    def _selected_providers(self) -> list[str]:
        return [
            provider for provider, check in self.provider_checks.items()
            if check.isChecked() and provider in self._allowed_providers
        ]

    def _refresh_controls(self) -> None:
        busy = self._worker is not None and self._worker.isRunning()
        ready = (
            self._status_loaded
            and self._consult_enabled
            and bool(self.thread_id)
            and bool(self._selected_providers())
            and bool(self.goal.text().strip())
            and len(self.goal.text()) <= 4000
            and not self._approval_ids
        )
        self.send_button.setEnabled(not busy and ready)
        self.close_button.setEnabled(not busy)
        for provider, check in self.provider_checks.items():
            check.setEnabled(not busy and provider in self._allowed_providers)

    def _start_request(
        self,
        action: str,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        if self._worker is not None and self._worker.isRunning():
            return
        worker = _ConsultationWorker(self.api_url, action, method, path, payload)
        worker.completed.connect(self._on_request_completed)
        worker.finished.connect(self._on_worker_finished)
        self._worker = worker
        self._refresh_controls()
        worker.start()

    def _enqueue(self) -> None:
        if not self.thread_id:
            self.status.setText("Abre uma conversa antes de pedir ajuda.")
            return
        providers = self._selected_providers()
        goal = self.goal.text().strip()
        if not providers or not goal:
            self.status.setText("Escreve a pergunta e seleciona pelo menos um provider permitido.")
            return
        self.status.setText("A registar a consulta na fila local; ainda não foi enviada ao browser.")
        self._start_request(
            "enqueue",
            "POST",
            "/recovery/browser-consult/enqueue",
            {
                "task_ref": "mobile-thread:" + self.thread_id,
                "goal": goal,
                "context": "",
                "providers": providers,
                # The server allowlist is the local operator's free-tier configuration.
                "free_capacity_confirmed": True,
            },
        )

    def _approve_next(self) -> None:
        if not self._approval_ids:
            message = (
                f"Consulta autorizada e aprovada na fila local para "
                f"{self._approved_count}/{self._approval_total} provider(s). "
                "Ainda não foi enviada: a extensão Chrome tem de estar emparelhada, "
                "com consultas ativadas e com os separadores dos providers disponíveis. "
                "As respostas recebidas aparecerão nesta conversa."
            )
            self.status.setText(message)
            self.status_message.emit(message)
            self._refresh_controls()
            return
        consultation_id = self._approval_ids.pop(0)
        self._start_request(
            "approve",
            "POST",
            "/recovery/browser-consult/approve/" + consultation_id,
        )

    def _on_request_completed(self, action: str, payload: object, error: str) -> None:
        if error:
            self._approval_ids.clear()
            self._continue_approval = False
            self.status.setText(
                "A consulta não foi concluída com segurança. Verifica o estado da fila antes de repetir. "
                + error
            )
            self._refresh_controls()
            return

        data = payload if isinstance(payload, dict) else {}
        if action == "status":
            self._status_loaded = True
            self._consult_enabled = data.get("enabled") is True
            self._allowed_providers = set(data.get("free_providers_allowlisted") or [])
            for provider, check in self.provider_checks.items():
                if provider not in self._allowed_providers:
                    check.setChecked(False)
            if not self._consult_enabled:
                self.status.setText("Consultas browser desativadas neste PC.")
            elif not self._allowed_providers:
                self.status.setText("Nenhum provider gratuito está configurado na allowlist local.")
            else:
                self.status.setText(
                    "Disponíveis: " + ", ".join(
                        label for provider, label in self.PROVIDERS
                        if provider in self._allowed_providers
                    )
                )
            self._refresh_controls()
            return

        if action == "enqueue":
            ids = data.get("consultation_ids")
            if not isinstance(ids, list) or not ids:
                self.status.setText(
                    "Nenhuma consulta foi criada. Estado: " + str(data.get("status") or "desconhecido")
                )
                self._refresh_controls()
                return
            self._approval_ids = [item for item in ids if isinstance(item, str)]
            self._approval_total = len(self._approval_ids)
            self._approved_count = 0
            self._continue_approval = True
            self.status.setText("Consulta registada. A aplicar a autorização explícita desta mensagem…")
            return

        if action == "approve":
            self._approved_count += 1
            self._continue_approval = True

    def _on_worker_finished(self) -> None:
        self._worker = None
        if self._continue_approval:
            self._continue_approval = False
            self._approve_next()
        self._refresh_controls()
