"""Operator-reviewed AI consultation dialog for the desktop cockpit.

This UI only previews and queues requests through the authenticated local API.
The paired browser extension remains the provider transport; no provider is
contacted directly by this dialog.
"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
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
        ("claude", "Claude"),
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
        self._loaded_mission_id: str | None = None
        self._worker: _ConsultationWorker | None = None
        self._preview_sha256: str | None = None
        self._approval_ids: list[str] = []
        self._result_ids: list[str] = []
        self._result_index = 0
        self._result_entries: list[str] = []
        self._pending_result_start = False
        self._approved_count = 0
        self._queued_count = 0
        self._pending_approval_start = False
        self._status_loaded = False
        self._consult_enabled = False
        self._status_requested = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowTitle("Pedir ajuda a uma IA — DGM-MAT")
        self.resize(760, 680)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "A consulta é enviada apenas para a fila local. A extensão Chrome "
            "emparelhada faz o transporte pela interface visível do fornecedor. "
            "Claude está disponível através do separador Claude no browser; Codex e Claude Code continuam a ser agentes locais separados."
        ))

        mission_row = QHBoxLayout()
        self.mission_id = QLineEdit()
        self.mission_id.setPlaceholderText("mission_1234abcd")
        self.mission_id.textChanged.connect(self._on_mission_id_changed)
        self.load_context_button = QPushButton("Carregar contexto da missão")
        self.load_context_button.clicked.connect(self._load_mission_context)
        mission_row.addWidget(self.mission_id, 1)
        mission_row.addWidget(self.load_context_button)
        layout.addWidget(QLabel("ID de missão opcional — carrega o checkpoint durável, limitado e redigido:"))
        layout.addLayout(mission_row)
        self.mission_context_info = QLabel("Ainda não foi carregado contexto de missão.")
        self.mission_context_info.setWordWrap(True)
        layout.addWidget(self.mission_context_info)

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

        self.results_button = QPushButton("Atualizar resultados das consultas")
        self.results_button.setEnabled(False)
        self.results_button.clicked.connect(self._refresh_results)
        layout.addWidget(self.results_button)
        self.results = QPlainTextEdit()
        self.results.setReadOnly(True)
        self.results.setPlaceholderText(
            "As respostas e os estados finais das consultas aprovadas aparecerão aqui. "
            "Todas as respostas externas permanecem por verificar."
        )
        self.results.setMaximumBlockCount(500)
        layout.addWidget(self.results, 1)

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
        self.load_context_button.setEnabled(not busy and self._queued_count == 0)
        self.send_button.setEnabled(not busy and ready)
        self.cancel_button.setEnabled(not busy)
        self.results_button.setEnabled(
            not busy and bool(self._result_ids) and self._queued_count == 0
        )

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

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._status_requested:
            self._status_requested = True
            self._request_status()

    def _request_status(self) -> None:
        self.status.setText("A verificar se a consulta browser está ativada e quais os fornecedores permitidos…")
        self._start_request("status", "GET", "/recovery/browser-consult/status")

    def _on_mission_id_changed(self, value: str) -> None:
        if self._loaded_mission_id and value.strip() != self._loaded_mission_id:
            self._loaded_mission_id = None
            self.mission_context_info.setText("O ID da missão mudou. Carrega novamente o contexto antes de associar a consulta.")
            self._refresh_controls()

    def _load_mission_context(self) -> None:
        mission_id = self.mission_id.text().strip()
        if not re.fullmatch(r"mission_[0-9a-f]{8}", mission_id):
            self.status.setText("Indica um ID de missão válido no formato mission_1234abcd.")
            return
        self.status.setText("A carregar contexto do checkpoint local. Nenhum fornecedor será contactado.")
        self._start_request(
            "mission-context",
            "POST",
            "/recovery/browser-consult/mission-context",
            {"mission_id": mission_id},
        )

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
        task_ref = (
            self._loaded_mission_id
            if self._loaded_mission_id
            else "mobile-thread:" + self.thread_id
        )
        payload = {
            "task_ref": task_ref,
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
                "A extensão Chrome emparelhada terá de estar ativa para executar o transporte visível. "
                "Quando terminar, atualiza os resultados para consultar as respostas."
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
            if action == "result":
                self._result_entries.append(
                    "Consulta " + str(self._result_ids[self._result_index])
                    + "\nFalha ao recuperar o resultado: " + error
                )
                self._result_index += 1
                self._pending_result_start = True
                return
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

        if action == "mission-context":
            goal = data.get("goal")
            context = data.get("context")
            if not isinstance(goal, str) or not isinstance(context, str):
                self.status.setText("O checkpoint não devolveu contexto utilizável; nada foi enviado.")
                return
            self.goal.setPlainText(goal)
            self.context.setPlainText(context)
            self._preview_sha256 = None
            mission_id = str(data.get("mission_id") or self.mission_id.text().strip())
            if not re.fullmatch(r"mission_[0-9a-f]{8}", mission_id):
                self.status.setText("O backend devolveu um ID de missão inválido; a consulta não será associada.")
                return
            self._loaded_mission_id = mission_id
            mission_status = str(data.get("mission_status") or "unknown")
            digest = str(data.get("context_sha256") or "")
            source = str(data.get("source") or "unknown")
            self.mission_context_info.setText(
                f"Origem: {source} | Missão: {mission_id} | Estado: {mission_status} | "
                f"Contexto SHA-256: {digest[:16] or 'n/d'} | "
                f"Fornecedor contactado: {'sim' if data.get('provider_contacted') else 'não'}"
            )
            self.status.setText(
                "Contexto de missão carregado. Revê e edita o pedido/contexto; "
                "gera uma nova pré-visualização antes de qualquer consulta."
            )
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
            self._result_ids = list(self._approval_ids)
            self._result_index = 0
            self._result_entries = []
            self.results.clear()
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
            return

        if action == "result":
            consultation_id = str(data.get("consultation_id") or self._result_ids[self._result_index])
            status = str(data.get("status") or "UNKNOWN")
            provider = str(data.get("provider") or "unknown")
            task_ref = str(data.get("task_ref") or "unknown")
            response_text = data.get("response_text")
            response_hash = str(data.get("response_sha256") or "n/d")
            lines = [
                f"CONSULTA: {consultation_id}",
                f"FORNECEDOR: {provider}",
                f"ASSOCIAÇÃO: {task_ref}",
                f"ESTADO: {status}",
                f"CRIADA: {data.get('created_at') or 'n/d'}",
                f"CONCLUÍDA: {data.get('completed_at') or 'n/d'}",
                f"ERRO CLASSIFICADO: {data.get('error_type') or 'nenhum registado'}",
                f"RESPOSTA SHA-256: {response_hash}",
                "CONFIANÇA: não verificada | Independência: não atestada | Aceite: não",
            ]
            if isinstance(response_text, str) and response_text.strip():
                lines.extend(["", "RESPOSTA DO FORNECEDOR:", response_text])
            else:
                lines.extend(["", "Ainda não existe resposta final guardada para esta consulta."])
            self._result_entries.append("\n".join(lines))
            self._result_index += 1
            self._pending_result_start = True

    def _refresh_results(self) -> None:
        if not self._result_ids:
            self.status.setText("Ainda não existem consultas associadas a esta janela.")
            return
        self._result_index = 0
        self._result_entries = []
        self.results.clear()
        self.status.setText("A recuperar os recibos persistentes das consultas. Apenas leitura; nenhuma ação será executada.")
        self._read_next_result()

    def _read_next_result(self) -> None:
        if self._result_index >= len(self._result_ids):
            self.results.setPlainText("\n\n" + ("=" * 72) + "\n\n".join(self._result_entries))
            self.status.setText(
                f"Leitura concluída: {len(self._result_entries)} recibo(s). "
                "As respostas são propostas externas não verificadas; não foram aceites nem executadas."
            )
            self._refresh_controls()
            return
        consultation_id = self._result_ids[self._result_index]
        self._start_request(
            "result",
            "GET",
            "/recovery/browser-consult/result/" + quote(consultation_id, safe=""),
        )

    def _on_worker_finished(self) -> None:
        self._worker = None
        if self._pending_approval_start:
            self._pending_approval_start = False
            self._approve_next()
        elif self._pending_result_start:
            self._pending_result_start = False
            self._read_next_result()
        else:
            self._refresh_controls()

    def closeEvent(self, event) -> None:
        if self._worker is not None and self._worker.isRunning():
            self.status.setText("Aguarda que o pedido local termine antes de fechar.")
            event.ignore()
            return
        super().closeEvent(event)
