# Path: C:\ProgramasGodMode\DGM-MAT\cockpit\widgets\command_console.py
"""Non-blocking desktop command console for the local DGM-MAT runtime."""
from __future__ import annotations

import html
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
    """Run all HTTP work outside the Qt GUI thread and return bounded results."""

    completed = Signal(str, str, str)

    def __init__(self, api_url: str, directive: str, *, status_only: bool = False):
        super().__init__()
        self.api_url = api_url.rstrip("/")
        self.directive = directive
        self.status_only = status_only

    def run(self) -> None:
        try:
            if self.status_only:
                response = authenticated_request("GET", f"{self.api_url}/status", timeout=(2, 8))
                if response.status_code != 200:
                    self.completed.emit(
                        "Error",
                        f"Could not retrieve runtime status (HTTP {response.status_code}).",
                        "error",
                    )
                    return
                data = response.json()
                resources = data.get("resources") or {}
                message = chr(10).join([
                    "--- RUNTIME OPERATIONAL STATUS ---",
                    f"Status: [{str(data.get('status', 'unknown')).upper()}]",
                    f"Degraded: {bool(data.get('is_degraded', False))}",
                    f"CPU: {resources.get('cpu', 'n/a')}% | MEM: {resources.get('memory', 'n/a')}%",
                    f"Active Missions: {data.get('missions_active', 0)}",
                    "---",
                ])
                self.completed.emit("Status", message, "system")
                return

            response = authenticated_request(
                "POST", f"{self.api_url}/missions",
                json={
                    "goal": self.directive,
                    "description": "Directive from desktop cockpit",
                },
                timeout=(2, 10),
            )
            if response.status_code not in (200, 201):
                self.completed.emit(
                    "Error",
                    f"Mission request failed (HTTP {response.status_code}). No success was assumed.",
                    "error",
                )
                return
            data: dict[str, Any] = response.json()
            mission_id = data.get("mission_id")
            if data.get("status") == "success" and mission_id:
                self.completed.emit("Runtime", f"Mission created: {mission_id}", "info")
            else:
                self.completed.emit(
                    "Error",
                    "Runtime response did not confirm mission creation.",
                    "error",
                )
        except LocalApiAuthenticationError:
            self.completed.emit(
                "Error",
                "Local API authentication is unavailable. Check the local runtime and bootstrap setup.",
                "error",
            )
        except requests.Timeout:
            self.completed.emit(
                "Error",
                "Runtime request timed out. The outcome may be unknown; check Missions before retrying.",
                "error",
            )
        except requests.RequestException:
            self.completed.emit(
                "Error",
                "Could not communicate with the local runtime. Check the runtime connection.",
                "error",
            )
        except (ValueError, TypeError, AttributeError):
            self.completed.emit(
                "Error",
                "Runtime returned an invalid response. No success was assumed.",
                "error",
            )


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

        header = QLabel("COGNITIVE TERMINAL")
        header.setStyleSheet(
            "font-weight: bold; color: #00ff00; font-size: 12px; font-family: 'Consolas';"
        )
        layout.addWidget(header)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(
            "background-color: #0f0f0f; color: #d4d4d4; "
            "font-family: 'Consolas', 'Courier New', monospace; "
            "border: none; line-height: 1.4;"
        )
        self.output.setFont(QFont("Consolas", 10))
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

        self.send_btn = QPushButton("ENVIAR")
        self.send_btn.setStyleSheet(
            "background-color: #007acc; color: white; font-weight: bold; "
            "padding: 8px 20px; border-radius: 3px;"
        )
        self.send_btn.clicked.connect(self._handle_command)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)
        layout.addWidget(input_container)

        self._append_message(
            "Sistema",
            "Consola pronta. As operações de rede decorrem em segundo plano.",
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
            self.input_field.setPlaceholderText("Runtime offline - input disabled")
        elif busy:
            self.input_field.setPlaceholderText("Waiting for runtime...")
        else:
            self.input_field.setPlaceholderText("Type a directive...")

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
