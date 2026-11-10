"""Operator-reviewed AI consultation dialog for the desktop cockpit.

This UI only previews and queues requests through the authenticated local API.
The paired browser extension remains the provider transport; no provider is
contacted directly by this dialog.
"""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from cockpit.api_client import authenticated_request, LocalApiAuthenticationError


class _ConsultationWorker(QThread):
    completed = Signal(str, object, str)

    def __init__(
        self,
        api_url: str,
        action: str,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        super().__init__()
        self.api_url = api_url.rstrip("/")
        self.action = action
        self.method = method
        self.path = path
        self.payload = payload

    def run(self) -> None:
        try:
            origin = self.api_url.rsplit("/runtime", 1)[0]
            if origin == self.api_url:
                raise ValueError("URL base do runtime não é válida.")
            response = authenticated_request(
                self.method,
                f"{origin}{self.path}",
                json=self.payload,
                timeout=(2, 12),
            )
            if response.status_code not in (200, 201):
                self.completed.emit(
                    self.action,
                    None,
                    f"Pedido recusado pelo backend (HTTP {response.status_code}). "
                    f"{response.text[:300]}",
                )
                return
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("O backend devolveu uma resposta inválida.")
            self.completed.emit(self.action, data, "")
        except LocalApiAuthenticationError:
            self.completed.emit(
                self.action, None, "Sessão local não autenticada. Volta a ligar o cockpit."
            )
        except Exception as exc:
            self.completed.emit(
                self.action, None,
                str(exc)[:400] or "Não foi possível comunicar com o backend local.",
            )


class AIConsultationDialog(QDialog):
    """Preview, explicit free-capacity attestation, queue and approval gate."""

    PROVIDERS = (
        ("chatgpt", "ChatGPT"),
        ("gemini", "Gemini"),
        ("grok", "Grok"),
        ("deepseek", "DeepSeek"),
        ("qwen", "Qwen"),
    )

    def __init__(
        self,
        api_url: str,
        thread_id: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.api_url = api_url
        self.thread_id = thread_id
        self._worker: _ConsultationWorker | None = None
        self._preview_sha256: str | None = None
        self._approval_ids: list[str] = []
        self._approved_count = 0
        self._queued_count = 0
        self._pending_approval_start = False
        self._status_loaded = False
        self._consult_enabled = False
        self._setup_ui()
        self._request_status()

    def _setup_ui(self) -> None:
        self.setWindowTitle("Pedir ajuda a uma IA — DGM-MAT")
        self.resize(760, 680)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "A consulta é enviada apenas para a fila local. A extensão Chrome "
            "emparelhada faz o transporte pela interface visível do fornecedor. "
            "Claude ainda não está configurado nesta via; Codex e Claude Code são agentes locais separados."
        ))

        form = QFormLayout()
        self.goal = QPlainTextEdit()
        self.goal.setPlaceholderText("O que queres que a IA analise? (máx. 4000 caracteres)")
        self.goal.setMaximumBlockCount(80)
        self.goal.textChanged.connect(self._invalidate_preview)
        self.goal.setFixedHeight(90)
        form.addRow("Pedido", self.goal)

        self.context = QPlainTextEdit()
        self.context.setPlaceholderText(
            "Contexto relevante e não confidencial: erro, ficheiros, branch, testes. "
            "Não incluas passwords, tokens, cookies ou chaves."
        )
        self.context.textChanged.connect(self._invalidate_preview)
        self.context.setFixedHeight(110)
        form.addRow("Contexto", self.context)
        layout.addLayout(form)

        layout.addWidget(QLabel("Fornecedores disponíveis neste transporte browser:"))
        provider_row = QHBoxLayout()
        self.provider_checks: dict[str, QCheckBox] = {}
        for provider, label in self.PROVIDERS:
            checkbox = QCheckBox(label)
            checkbox.setChecked(provider == "chatgpt")
            checkbox.toggled.connect(self._refresh_controls)
            self.provider_checks[provider] = checkbox
            provider_row.addWidget(checkbox)
        layout.addLayout(provider_row)

        self.free_capacity = QCheckBox(
            "Confirmo que as contas selecionadas são gratuitas e têm capacidade disponível."
        )
        self.free_capacity.toggled.connect(self._refresh_controls)
        layout.addWidget(self.free_capacity)

        self.preview_button = QPushButton("Gerar pré-visualização")
        self.preview_button.clicked.connect(self._request_preview)
        layout.addWidget(self.preview_button)

        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText(
            "O prompt exato, já sujeito à redação de segredos, aparecerá aqui."
        )
        layout.addWidget(self.preview, 1)

        self.status = QLabel("Nenhum pedido foi enviado.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        buttons = QHBoxLayout()
        self.send_button = QPushButton("Confirmar e colocar na fila")
        self.send_button.setEnabled(False)
        self.send_button.clicked.connect(self._enqueue)
        self.cancel_button = QPushButton("Fechar")
        self.cancel_button.clicked.connect(self.reject)
        buttons.addWidget(self.send_button)
        buttons.addWidget(self.cancel_button)
        layout.addLayout(buttons)

    def _selected_providers(self) -> list[str]:
        return [
            provider for provider, checkbox in self.provider_checks.items()
            if checkbox.isChecked()
        ]

    def _invalidate_preview(self) -> None:
        self._preview_sha256 = None
        self._refresh_controls()

    def _refresh_controls(self) -> None:
        busy = self._worker is not None and self._worker.isRunning()
        ready = (
            self._status_loaded
            and self._consult_enabled
            and bool(self._preview_sha256)
            and bool(self._selected_providers())
            and self.free_capacity.isChecked()
            and bool(self.goal.toPlainText().strip())
            and len(self.goal.toPlainText()) <= 4000
            and len(self.context.toPlainText()) <= 4000
            and self._queued_count == 0
        )
        self.preview_button.setEnabled(not busy and self._queued_count == 0)
        self.send_button.setEnabled(not busy and ready)
        self.cancel_button.setEnabled(not busy)

    def _start_request(
        self,
        action: str,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        if self._worker is not None and self._worker.isRunning():
            return
        worker = _ConsultationWorker(
            self.api_url, action, method, path, payload
        )
        worker.completed.connect(self._on_request_completed)
        worker.finished.connect(self._on_worker_finished)
        self._worker = worker
        self._refresh_controls()
        worker.start()

    def _request_status(self) -> None:
        self.status.setText("A verificar se a consulta browser está ativada e quais os fornecedores permitidos…")
        self._start_request("status", "GET", "/recovery/browser-consult/status")

    def _request_preview(self) -> None:
        goal = self.goal.toPlainText().strip()
        context = self.context.toPlainText()
        if not goal or len(goal) > 4000 or len(context) > 4000:
            self.status.setText("O pedido deve ter 1–4000 caracteres e o contexto até 4000.")
            return
        self._preview_sha256 = None
        self.preview.clear()
        self.status.setText("A gerar pré-visualização redigida. Nenhum fornecedor será contactado.")
        self._start_request(
            "preview",
            "POST",
            "/recovery/browser-consult/preview",
            {"goal": goal, "context": context},
        )

    def _enqueue(self) -> None:
        if not self._preview_sha256:
            self.status.setText("Gera uma nova pré-visualização antes de confirmar.")
            return
        providers = self._selected_providers()
        if not providers or not self.free_capacity.isChecked():
            self.status.setText("Seleciona pelo menos um fornecedor e confirma a capacidade gratuita.")
            return
        payload = {
            "task_ref": "mobile-thread:" + self.thread_id,
            "goal": self.goal.toPlainText().strip(),
            "context": self.context.toPlainText(),
            "providers": providers,
            "free_capacity_confirmed": True,
            "preview_sha256": self._preview_sha256,
        }
        self.status.setText("A registar a consulta. Ainda não foi libertada para a extensão.")
        self._start_request(
            "enqueue", "POST", "/recovery/browser-consult/enqueue", payload
        )

    def _approve_next(self) -> None:
        if not self._approval_ids:
            self.status.setText(
                f"Consulta aprovada e colocada na fila: {self._approved_count}/{self._queued_count}. "
                "A extensão Chrome emparelhada terá de estar ativa para executar o transporte visível."
            )
            self._refresh_controls()
            return
        consultation_id = self._approval_ids.pop(0)
        self._start_request(
            "approve",
            "POST",
            "/recovery/browser-consult/approve/" + consultation_id,
        )

    def _on_request_completed(
        self, action: str, payload: object, error: str
    ) -> None:
        if error:
            if action == "approve":
                self._approval_ids.clear()
                self.status.setText(
                    "A consulta foi criada, mas uma aprovação falhou. "
                    "Verifica o estado da fila antes de repetir. " + error
                )
            else:
                self.status.setText(error)
            self._refresh_controls()
            return

        data = payload if isinstance(payload, dict) else {}
        if action == "status":
            self._status_loaded = True
            self._consult_enabled = data.get("enabled") is True
            allowed = set(data.get("free_providers_allowlisted") or [])
            for provider, checkbox in self.provider_checks.items():
                available = provider in allowed
                checkbox.setEnabled(available)
                if not available:
                    checkbox.setChecked(False)
            if not self._consult_enabled:
                self.status.setText("Consulta externa desativada neste PC. A pré-visualização continua disponível, mas a fila não pode ser usada.")
            elif not allowed:
                self.status.setText("Consulta ativada, mas nenhum fornecedor browser está na allowlist deste PC.")
            else:
                self.status.setText("Consulta ativada. Fornecedores permitidos: " + ", ".join(sorted(allowed)))
            self._refresh_controls()
            return

        if action == "preview":
            prompt = data.get("prompt")
            digest = data.get("prompt_sha256")
            if not isinstance(prompt, str) or not isinstance(digest, str):
                self.status.setText("Pré-visualização inválida; nada foi colocado na fila.")
                return
            self.preview.setPlainText(prompt)
            self._preview_sha256 = digest
            redacted = bool(data.get("prompt_redacted"))
            self.status.setText(
                "Pré-visualização pronta"
                + (" — segredos detetados e removidos." if redacted else ".")
                + " Revê o texto e confirma a capacidade gratuita."
            )
            self._refresh_controls()
            return

        if action == "enqueue":
            ids = data.get("consultation_ids")
            if not isinstance(ids, list) or not ids:
                self.status.setText(
                    "O backend não colocou consultas na fila. Estado: "
                    + str(data.get("status") or "desconhecido")
                )
                return
            self._approval_ids = [str(item) for item in ids if isinstance(item, str)]
            self._queued_count = len(self._approval_ids)
            if not self._approval_ids:
                self.status.setText("A resposta do backend não contém IDs de consulta válidos.")
                return
            self.status.setText(
                f"{self._queued_count} consulta(s) criada(s). A aplicar a aprovação explícita…"
            )
            self._pending_approval_start = True
            return

        if action == "approve":
            self._approved_count += 1
            self._pending_approval_start = True

    def _on_worker_finished(self) -> None:
        self._worker = None
        if self._pending_approval_start:
            self._pending_approval_start = False
            self._approve_next()
        else:
            self._refresh_controls()

    def closeEvent(self, event) -> None:
        if self._worker is not None and self._worker.isRunning():
            self.status.setText("Aguarda que o pedido local termine antes de fechar.")
            event.ignore()
            return
        super().closeEvent(event)
