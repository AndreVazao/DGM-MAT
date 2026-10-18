# Path: C:\ProgramasGodMode\DGM-MAT\cockpit\widgets\command_console.py
"""Non-blocking desktop command console for the local DGM-MAT runtime."""
from __future__ import annotations

import html
import re
import time
import requests
from datetime import datetime
from typing import Any

from cockpit.api_client import authenticated_request, LocalApiAuthenticationError
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class _RuntimeRequestWorker(QThread):
    """Submit one mission, handle explicit queue decisions, and report real status."""

    completed = Signal(str, str, str)

    def __init__(self, api_url: str, directive: str, *, status_only: bool = False):
        super().__init__()
        self.api_url = api_url.rstrip("/")
        self.directive = directive
        self.status_only = status_only

    def _request(self, method: str, suffix: str, **kwargs):
        return authenticated_request(
            method, f"{self.api_url}{suffix}", **kwargs
        )

    def _mission(self, mission_id: str) -> dict[str, Any] | None:
        response = self._request("GET", "/missions", timeout=(2, 5))
        if response.status_code != 200:
            raise RuntimeError(f"Não foi possível consultar as missões (HTTP {response.status_code}).")
        data = response.json()
        if not isinstance(data, list):
            raise ValueError("O runtime devolveu uma lista de missões inválida.")
        return next(
            (item for item in data if isinstance(item, dict) and item.get("mission_id") == mission_id),
            None,
        )

    def _finish_from_mission(self, mission: dict[str, Any]) -> bool:
        status = str(mission.get("status", "UNKNOWN")).upper()
        mission_id = str(mission.get("mission_id", "desconhecida"))
        result = mission.get("result") or (mission.get("metadata") or {}).get("result") or {}
        output = mission.get("output") or result.get("output") or result.get("summary")

        if status == "COMPLETED":
            self.completed.emit(
                "DGM-MAT",
                f"Missão concluída ({mission_id}).\n{output or 'O runtime confirmou conclusão, mas não devolveu texto de resultado.'}",
                "info",
            )
            return True
        if status == "FAILED":
            self.completed.emit(
                "DGM-MAT",
                f"Missão falhou ({mission_id}).\n{mission.get('error') or result.get('error') or output or 'O runtime não forneceu detalhes do erro.'}",
                "error",
            )
            return True
        if status == "CANCELLED":
            self.completed.emit(
                "Sistema",
                f"Missão cancelada ({mission_id}).\n{mission.get('error') or 'A ação foi recusada pelo operador.'}",
                "system",
            )
            return True
        if status == "WAITING_FOR_USER":
            intervention = (mission.get("metadata") or {}).get("human_intervention") or {}
            self.completed.emit(
                "DGM-MAT",
                f"A missão ({mission_id}) precisa da tua intervenção.\n{intervention.get('instructions') or intervention.get('reason') or 'Consulta o pedido de intervenção na missão.'}",
                "system",
            )
            return True
        if status == "APPROVAL_PENDING":
            self.completed.emit(
                "DGM-MAT",
                f"A missão ({mission_id}) aguarda uma decisão de aprovação.",
                "system",
            )
            return True
        return False

    def _poll_mission(self, mission_id: str, *, timeout_seconds: int = 65) -> None:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            mission = self._mission(mission_id)
            if mission is None:
                raise RuntimeError(f"A missão {mission_id} ainda não aparece na consulta do runtime.")
            if self._finish_from_mission(mission):
                return

            status = str(mission.get("status", "UNKNOWN")).upper()
            action_status = str(mission.get("action_status") or "").upper()
            action_id = mission.get("action_id")
            if status == "QUEUED" and action_status == "QUEUED":
                self.completed.emit(
                    "DGM-MAT",
                    f"Missão registada ({mission_id}), mas aguarda aprovação explícita da ação {action_id}. "
                    f"Se confirmares, escreve: aprovar ação {action_id}. Para recusar: rejeitar ação {action_id} motivo.",
                    "system",
                )
                return
            time.sleep(2)

        self.completed.emit(
            "Sistema",
            f"A missão {mission_id} continua sem estado final após {timeout_seconds}s. "
            "Não voltei a submetê-la para evitar duplicar trabalho. Verifica o runtime e consulta a missão antes de repetir.",
            "error",
        )

    def _handle_queue_decision(self, directive: str) -> bool:
        approve = re.fullmatch(r"\s*(?:aprovar|approve)\s+(?:a\s+)?(?:ação|action)\s+(\d+)\s*", directive, re.IGNORECASE)
        reject = re.fullmatch(r"\s*(?:rejeitar|rejeita|reject)\s+(?:a\s+)?(?:ação|action)\s+(\d+)(?:\s+(.+))?\s*", directive, re.IGNORECASE)
        if not approve and not reject:
            return False

        action_id = int((approve or reject).group(1))
        if approve:
            response = self._request("POST", f"/queue/actions/{action_id}/approve", timeout=(2, 8))
        else:
            reason = (reject.group(2) or "Recusado pelo operador no cockpit.").strip()
            response = self._request(
                "POST", f"/queue/actions/{action_id}/reject",
                json={"reason": reason}, timeout=(2, 8),
            )
        if response.status_code != 200:
            detail = response.text[:500]
            self.completed.emit("Erro", f"A decisão sobre a ação {action_id} não foi aceite (HTTP {response.status_code}). {detail}", "error")
            return True

        payload = response.json()
        if reject:
            self.completed.emit(
                "Sistema",
                f"Ação {action_id} recusada. Missão associada: {payload.get('mission_id') or 'nenhuma'}.",
                "system",
            )
            return True

        self.completed.emit("Sistema", f"Ação {action_id} aprovada. A acompanhar o estado real da missão…", "system")
        mission_id = None
        queue_response = self._request("GET", "/queue", timeout=(2, 8))
        if queue_response.status_code == 200:
            queue_data = queue_response.json()
            actions = queue_data.get("recent_actions", []) if isinstance(queue_data, dict) else []
            action = next((item for item in actions if int(item.get("id", -1)) == action_id), None)
            if action:
                mission_id = (action.get("payload") or {}).get("mission_id")
        if mission_id:
            self._poll_mission(str(mission_id))
        else:
            self.completed.emit("Sistema", "A decisão foi registada, mas a ação não está ligada a uma missão consultável.", "system")
        return True

    def run(self) -> None:
        try:
            if self.status_only:
                response = self._request("GET", "/status", timeout=(2, 8))
                if response.status_code != 200:
                    self.completed.emit("Erro", f"Não foi possível consultar o runtime (HTTP {response.status_code}).", "error")
                    return
                data = response.json()
                resources = data.get("resources") or {}
                message = "\n".join([
                    "--- ESTADO OPERACIONAL ---",
                    f"Estado: {str(data.get('status', 'desconhecido')).upper()}",
                    f"Degradado: {bool(data.get('is_degraded', False))}",
                    f"CPU: {resources.get('cpu', 'n/d')}% | Memória: {resources.get('memory', 'n/d')}%",
                    f"Missões ativas: {data.get('missions_active', 0)}",
                ])
                self.completed.emit("Sistema", message, "system")
                return

            if self._handle_queue_decision(self.directive):
                return

            response = self._request(
                "POST", "/missions",
                json={"goal": self.directive, "description": "Pedido enviado pelo cockpit de chat"},
                timeout=(2, 10),
            )
            if response.status_code not in (200, 201):
                self.completed.emit("Erro", f"O runtime recusou o pedido (HTTP {response.status_code}). Não foi assumido sucesso.", "error")
                return
            data: dict[str, Any] = response.json()
            mission_id = data.get("mission_id")
            if data.get("status") != "success" or not mission_id:
                self.completed.emit("DGM-MAT", f"O pedido não foi aceite. {data.get('error') or 'Resposta sem confirmação de criação.'}", "error")
                return

            self.completed.emit(
                "Sistema",
                f"Missão registada: {mission_id} | estado: {data.get('mission_status', 'desconhecido')}.",
                "system",
            )
            self._poll_mission(str(mission_id))
        except LocalApiAuthenticationError:
            self.completed.emit("Erro", "Não foi possível autenticar no runtime local. Verifica o serviço e a configuração de acesso local.", "error")
        except requests.Timeout:
            self.completed.emit("Erro", "O pedido HTTP excedeu o tempo limite. O resultado pode ser desconhecido; consulta a missão antes de voltar a enviá-la.", "error")
        except requests.RequestException:
            self.completed.emit("Erro", "Não foi possível comunicar com o runtime local. Verifica a ligação ao serviço.", "error")
        except (RuntimeError, ValueError, TypeError, AttributeError) as exc:
            self.completed.emit("Erro", str(exc) or "O runtime devolveu uma resposta inválida.", "error")


class CommandConsoleWidget(QWidget):
    """Chat-like command console whose network requests never block the GUI."""

    def __init__(self):
        super().__init__()
        self.history: list[dict[str, str]] = []
        self.api_url = "http://127.0.0.1:8181/runtime"
        self._worker: _RuntimeRequestWorker | None = None
        self._runtime_available = True
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        header = QLabel("DGM-MAT — CHAT DE MISSÕES")
        header.setStyleSheet(
            "font-weight: bold; color: #4ec9b0; font-size: 12px;"
        )
        layout.addWidget(header)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(
            "background-color: #17191d; color: #e5e7eb; "
            "font-family: 'Segoe UI', sans-serif; "
            "border: none; line-height: 1.4;"
        )
        self.output.setFont(QFont("Segoe UI", 10))
        layout.addWidget(self.output, 1)

        input_container = QFrame()
        input_container.setStyleSheet(
            "background-color: #252526; border-top: 1px solid #3e3e3e;"
        )
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(5, 5, 5, 5)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Escreve uma instrução...")
        self.input_field.setStyleSheet(
            "background-color: #3c3c3c; color: #ffffff; "
            "border: 1px solid #505050; padding: 8px; border-radius: 3px;"
        )
        self.input_field.returnPressed.connect(self._handle_command)

        self.send_btn = QPushButton("Enviar")
        self.send_btn.setStyleSheet(
            "background-color: #2563eb; color: white; font-weight: bold; "
            "padding: 8px 20px; border-radius: 6px;"
        )
        self.send_btn.clicked.connect(self._handle_command)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)
        layout.addWidget(input_container)

        self._append_message(
            "Sistema",
            "Estou ligado ao backend local. Envia uma missão em linguagem natural. Quando uma ação pedir aprovação, escreve “aprovar ação ID” ou “rejeitar ação ID motivo”. Só apresento uma missão como concluída quando o backend devolver o estado final.",
            "system",
        )

    def set_enabled(self, enabled: bool) -> None:
        self._runtime_available = bool(enabled)
        self._refresh_controls()

    def _refresh_controls(self) -> None:
        busy = self._worker is not None and self._worker.isRunning()
        available = self._runtime_available and not busy
        self.input_field.setEnabled(available)
        self.send_btn.setEnabled(available)
        if not self._runtime_available:
            self.input_field.setPlaceholderText("Runtime offline — envio desativado")
        elif busy:
            self.input_field.setPlaceholderText("À espera do backend…")
        else:
            self.input_field.setPlaceholderText("Escreve uma missão…")

    def _handle_command(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return
        directive = self.input_field.text().strip()
        if not directive:
            return

        self.input_field.clear()
        self._append_message("Tu", directive, "user")
        # Deliberately do not log the directive: it may contain private information.
        self._start_request(directive, status_only=directive.casefold() == "runtime status")

    def _process_directive(self, directive: str) -> None:
        """Compatibility entry point; dispatches work asynchronously."""
        if self._worker is not None and self._worker.isRunning():
            self._append_message("Sistema", "Já existe um pedido em curso.", "error")
            return
        self._start_request(
            directive,
            status_only=directive.casefold().strip() == "runtime status",
        )

    def _handle_runtime_status(self) -> None:
        """Compatibility entry point for the runtime status command."""
        if self._worker is None or not self._worker.isRunning():
            self._start_request("", status_only=True)

    def _start_request(self, directive: str, *, status_only: bool) -> None:
        self._append_message("Sistema", "Pedido enviado ao runtime…", "system")
        worker = _RuntimeRequestWorker(self.api_url, directive, status_only=status_only)
        worker.completed.connect(self._on_request_completed)
        worker.finished.connect(self._on_worker_finished)
        self._worker = worker
        self.input_field.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.input_field.setPlaceholderText("Waiting for runtime...")
        worker.start()

    def _on_request_completed(self, sender: str, message: str, msg_type: str) -> None:
        self._append_message(sender, message, msg_type)

    def _on_worker_finished(self) -> None:
        worker = self.sender()
        if worker is self._worker:
            self._worker = None
        self._refresh_controls()

    def _append_message(self, sender: str, text: str, msg_type: str = "info") -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {
            "user": "#569cd6",
            "system": "#ce9178",
            "info": "#4ec9b0",
            "error": "#f44336",
        }
        color = colors.get(msg_type, "#d4d4d4")
        safe_sender = html.escape(str(sender))
        safe_text = html.escape(str(text)).replace(chr(10), "<br>")
        self.history.append(
            {"sender": str(sender), "text": str(text), "type": msg_type, "timestamp": timestamp}
        )
        html_message = (
            "<div style='margin-bottom: 8px;'>"
            f"<span style='color: #808080; font-size: 8pt;'>[{timestamp}]</span> "
            f"<b style='color: {color};'>{safe_sender}:</b>"
            f"<div style='margin-left: 15px; color: #d4d4d4;'>{safe_text}</div>"
            "</div>"
        )
        self.output.append(html_message)
        self.output.moveCursor(QTextCursor.End)
