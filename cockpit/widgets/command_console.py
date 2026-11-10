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
from cockpit.workspace.ai_consultation_dialog import AIConsultationDialog
from cockpit.mission_status_client import (
    fetch_mission_checkpoint,
    submit_mission_once,
    wait_for_mission_checkpoint,
)
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
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
        self._sleep = time.sleep

    def _request(self, method: str, suffix: str, **kwargs):
        return authenticated_request(
            method, f"{self.api_url}{suffix}", **kwargs
        )

    def _mission(self, mission_id: str) -> dict[str, Any] | None:
        return fetch_mission_checkpoint(mission_id, request=self._request)

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
        mission = wait_for_mission_checkpoint(
            mission_id,
            self._mission,
            timeout_seconds=timeout_seconds,
            sleep=self._sleep,
        )
        if mission is None:
            self.completed.emit(
                "Sistema",
                f"A missão {mission_id} continua sem estado final após {timeout_seconds}s. "
                "A consulta de estado não confirmou conclusão. Não voltei a submetê-la para evitar duplicar trabalho. "
                "Consulta esta missão antes de repetir.",
                "error",
            )
            return

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

            data = submit_mission_once(self._request, self.directive)
            mission_id = data["mission_id"]

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


class _ConversationRequestWorker(QThread):
    """Run one authenticated conversation API request away from the GUI thread."""

    completed = Signal(str, object, str)

    def __init__(
        self,
        api_url: str,
        action: str,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ):
        super().__init__()
        self.api_url = api_url.rstrip("/")
        self.action = action
        self.method = method
        self.path = path
        self.params = params
        self.payload = payload

    def run(self) -> None:
        try:
            origin = self.api_url.rsplit("/runtime", 1)[0]
            if origin == self.api_url:
                raise ValueError("URL base do runtime não é válida para o serviço de conversas.")
            response = authenticated_request(
                self.method,
                f"{origin}{self.path}",
                params=self.params,
                json=self.payload,
                timeout=(2, 8),
            )
            if response.status_code not in (200, 201):
                self.completed.emit(
                    self.action,
                    None,
                    f"Serviço de conversas recusou o pedido (HTTP {response.status_code}).",
                )
                return
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("O serviço de conversas devolveu uma resposta inválida.")
            self.completed.emit(self.action, data, "")
        except LocalApiAuthenticationError:
            self.completed.emit(self.action, None, "Não foi possível autenticar no serviço local.")
        except requests.RequestException:
            self.completed.emit(self.action, None, "Não foi possível comunicar com o histórico local.")
        except (ValueError, TypeError, KeyError) as exc:
            self.completed.emit(self.action, None, str(exc) or "Resposta inválida do histórico local.")


class CommandConsoleWidget(QWidget):
    """Chat-like command console whose network requests never block the GUI."""

    def __init__(self):
        super().__init__()
        self.history: list[dict[str, str]] = []
        self.api_url = "http://127.0.0.1:8181/runtime"
        self._worker: _RuntimeRequestWorker | None = None
        self._runtime_available = True
        self._active_thread_id: str | None = None
        self._active_thread_status = "active"
        self._pending_directive: str | None = None
        self._thread_create_active = False
        self._search_query = ""
        self._search_offset = 0
        self._search_has_more = False
        self._conversation_workers: set[_ConversationRequestWorker] = set()
        self._transcript_queue: list[tuple[str, str, str, str]] = []
        self._transcript_write_active = False
        self._threads_loaded = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        header = QLabel("DGM-MAT — CHAT DE MISSÕES")
        header.setStyleSheet(
            "font-weight: bold; color: #4ec9b0; font-size: 12px;"
        )
        layout.addWidget(header)

        history_bar = QHBoxLayout()
        self.new_thread_btn = QPushButton("＋ Nova conversa")
        self.new_thread_btn.clicked.connect(self._create_thread)
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Pesquisar conversas…")
        self.search_field.returnPressed.connect(self._search_threads)
        self.search_btn = QPushButton("Pesquisar")
        self.search_btn.clicked.connect(self._search_threads)
        self.ai_help_btn = QPushButton("Pedir ajuda a uma IA")
        self.ai_help_btn.clicked.connect(self._open_ai_consultation)
        self.search_more_btn = QPushButton("Mais resultados")
        self.search_more_btn.setEnabled(False)
        self.search_more_btn.clicked.connect(self._search_more_threads)
        self.archive_thread_btn = QPushButton("Arquivar / restaurar")
        self.archive_thread_btn.setEnabled(False)
        self.archive_thread_btn.clicked.connect(self._archive_selected_thread)
        history_bar.addWidget(self.new_thread_btn)
        history_bar.addWidget(self.search_field, 1)
        history_bar.addWidget(self.search_btn)
        history_bar.addWidget(self.ai_help_btn)
        history_bar.addWidget(self.search_more_btn)
        history_bar.addWidget(self.archive_thread_btn)
        layout.addLayout(history_bar)

        self.thread_list = QListWidget()
        self.thread_list.setMaximumHeight(112)
        self.thread_list.setStyleSheet(
            "background-color: #202328; color: #d4d4d4; "
            "border: 1px solid #3e3e3e;"
        )
        self.thread_list.itemClicked.connect(self._open_selected_thread)
        self.thread_list.itemSelectionChanged.connect(self._refresh_controls)
        layout.addWidget(self.thread_list)

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
        conversation_busy = (
            self._transcript_write_active
            or bool(self._pending_directive)
            or self._thread_create_active
        )
        available = self._runtime_available and not busy and not conversation_busy and self._active_thread_status == "active"
        self.input_field.setEnabled(available)
        self.send_btn.setEnabled(available)
        self.new_thread_btn.setEnabled(not busy and not conversation_busy)
        self.search_field.setEnabled(not busy and not conversation_busy)
        self.search_btn.setEnabled(not busy and not conversation_busy)
        self.search_more_btn.setEnabled(
            not busy and not conversation_busy and self._search_has_more
        )
        self.thread_list.setEnabled(not busy and not conversation_busy)
        self.archive_thread_btn.setEnabled(not busy and not conversation_busy and self.thread_list.currentItem() is not None)
        if not self._runtime_available:
            self.input_field.setPlaceholderText("Runtime offline — envio desativado")
        elif self._active_thread_status == "archived":
            self.input_field.setPlaceholderText("Conversa arquivada — restaura-a para continuar")
        elif busy:
            self.input_field.setPlaceholderText("À espera do backend…")
        else:
            self.input_field.setPlaceholderText("Escreve uma missão…")

    def _handle_command(self) -> None:
        if (
            (self._worker is not None and self._worker.isRunning())
            or self._pending_directive
            or self._transcript_write_active
            or self._thread_create_active
        ):
            return
        directive = self.input_field.text().strip()
        if not directive:
            return

        self.input_field.clear()
        self._pending_directive = directive
        if self._active_thread_id:
            self._persist_pending_user_message()
        else:
            self._create_thread(for_pending_send=True)

    def _process_directive(self, directive: str) -> None:
        """Compatibility entry point; persists the user entry before dispatch."""
        if (
            (self._worker is not None and self._worker.isRunning())
            or self._pending_directive
            or self._transcript_write_active
            or self._thread_create_active
        ):
            self._append_message("Sistema", "Já existe um pedido em curso.", "error")
            return
        normalized = directive.strip()
        if not normalized:
            return
        self._pending_directive = normalized
        if self._active_thread_id:
            self._persist_pending_user_message()
        else:
            self._create_thread(for_pending_send=True)

    def _handle_runtime_status(self) -> None:
        """Compatibility entry point for the runtime status command."""
        if (
            (self._worker is None or not self._worker.isRunning())
            and not self._pending_directive
            and not self._transcript_write_active
            and not self._thread_create_active
        ):
            self._pending_directive = "runtime status"
            if self._active_thread_id:
                self._persist_pending_user_message()
            else:
                self._create_thread(for_pending_send=True)

    def _start_request(self, directive: str, *, status_only: bool) -> None:
        self._append_message("Sistema", "Pedido enviado ao runtime…", "system")
        worker = _RuntimeRequestWorker(self.api_url, directive, status_only=status_only)
        worker.thread_id = self._active_thread_id
        worker.completed.connect(self._on_request_completed)
        worker.finished.connect(self._on_worker_finished)
        self._worker = worker
        self._refresh_controls()
        self.input_field.setPlaceholderText("À espera do backend…")
        worker.start()

    def _on_request_completed(self, sender: str, message: str, msg_type: str) -> None:
        worker = self.sender()
        thread_id = getattr(worker, "thread_id", None)
        self._append_message(sender, message, msg_type)
        if isinstance(thread_id, str) and thread_id:
            role = "assistant" if sender == "DGM-MAT" else "system"
            self._persist_transcript_entry(thread_id, role, message)

    def _on_worker_finished(self) -> None:
        worker = self.sender()
        if worker is self._worker:
            self._worker = None
        self._refresh_controls()


    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._threads_loaded:
            self._threads_loaded = True
            self._load_threads()

    def _conversation_request(
        self,
        action: str,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        worker = _ConversationRequestWorker(
            self.api_url, action, method, path, params=params, payload=payload
        )
        self._conversation_workers.add(worker)
        worker.completed.connect(self._on_conversation_request_completed)
        worker.finished.connect(lambda current=worker: self._conversation_workers.discard(current))
        worker.start()

    def _load_threads(self) -> None:
        self._conversation_request("threads-list", "GET", "/mobile/threads")

    def _open_ai_consultation(self) -> None:
        if not self._active_thread_id:
            self._append_message(
                "Sistema",
                "Cria ou abre uma conversa antes de pedir ajuda a uma IA. "
                "A resposta externa ficará associada a essa conversa.",
                "system",
            )
            return
        dialog = AIConsultationDialog(
            self.api_url,
            self._active_thread_id,
            self,
        )
        dialog.exec()

    def _create_thread(self, *, for_pending_send: bool = False) -> None:
        if self._worker is not None and self._worker.isRunning():
            return
        if self._thread_create_active:
            return
        self._thread_create_active = True
        self._refresh_controls()
        title = "Nova conversa"
        if for_pending_send and self._pending_directive:
            title = self._pending_directive[:72].strip() or title
        self._conversation_request(
            "thread-create", "POST", "/mobile/threads",
            payload={"title": title},
        )

    def _search_threads(self) -> None:
        query = self.search_field.text().strip()
        if len(query) < 2:
            self._append_message("Sistema", "A pesquisa precisa de pelo menos dois caracteres.", "system")
            return
        self._search_query = query
        self._search_offset = 0
        self._search_has_more = False
        self._refresh_controls()
        self._conversation_request(
            "thread-search", "GET", "/mobile/threads/search",
            params={"q": query, "limit": 25, "offset": 0},
        )

    def _search_more_threads(self) -> None:
        if not self._search_has_more or len(self._search_query) < 2:
            return
        self._conversation_request(
            "thread-search-more", "GET", "/mobile/threads/search",
            params={"q": self._search_query, "limit": 25, "offset": self._search_offset},
        )

    def _archive_selected_thread(self) -> None:
        item = self.thread_list.currentItem()
        if item is None:
            return
        thread_id = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(thread_id, str) or not thread_id:
            return
        status = str(item.data(Qt.ItemDataRole.UserRole + 1) or "active")
        action = "thread-restore" if status == "archived" else "thread-archive"
        endpoint = "restore" if status == "archived" else "archive"
        self._conversation_request(
            action, "POST", f"/mobile/threads/{thread_id}/{endpoint}"
        )

    def _open_selected_thread(self, item: QListWidgetItem) -> None:
        thread_id = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(thread_id, str) and thread_id:
            self._conversation_request(
                "thread-open", "GET", f"/mobile/threads/{thread_id}"
            )

    def _persist_pending_user_message(self) -> None:
        directive = self._pending_directive
        thread_id = self._active_thread_id
        if not directive or not thread_id:
            return
        self._transcript_queue.append(("send-user-entry", thread_id, "user", directive))
        self._flush_transcript_queue()

    def _persist_transcript_entry(self, thread_id: str, role: str, content: str) -> None:
        self._transcript_queue.append(("transcript-entry", thread_id, role, content))
        self._flush_transcript_queue()

    def _flush_transcript_queue(self) -> None:
        if self._transcript_write_active or not self._transcript_queue:
            return
        action, thread_id, role, content = self._transcript_queue.pop(0)
        self._transcript_write_active = True
        self._refresh_controls()
        self._conversation_request(
            action, "POST", f"/mobile/threads/{thread_id}/entries",
            payload={"role": role, "content": content},
        )

    def _on_conversation_request_completed(
        self, action: str, payload: object, error: str
    ) -> None:
        is_transcript_write = action in {"send-user-entry", "transcript-entry"}
        if is_transcript_write:
            self._transcript_write_active = False
        if action in {"thread-archive", "thread-restore"}:
            thread_id = data.get("id")
            status = str(data.get("status") or ("archived" if action == "thread-archive" else "active"))
            if isinstance(thread_id, str) and thread_id == self._active_thread_id:
                self._active_thread_status = status
            self._append_message(
                "Sistema",
                "Conversa arquivada sem apagar mensagens." if status == "archived" else "Conversa restaurada; podes continuar.",
                "system",
            )
            self._load_threads()
            self._refresh_controls()
            return

        if action == "thread-create":
            self._thread_create_active = False
        if error:
            if action == "send-user-entry":
                self._pending_directive = None
                self._append_message(
                    "Erro",
                    f"A mensagem não foi guardada no histórico; por segurança, a missão não foi enviada. {error}",
                    "error",
                )
            elif action == "thread-create":
                had_pending_message = bool(self._pending_directive)
                self._pending_directive = None
                message = (
                    f"A mensagem não foi guardada; a missão não foi enviada. {error}"
                    if had_pending_message
                    else f"Não foi possível criar uma nova conversa. {error}"
                )
                self._append_message("Erro", message, "error")
            elif action == "transcript-entry":
                self._append_message(
                    "Aviso",
                    "Uma atualização da conversa não pôde ser guardada no histórico local.",
                    "error",
                )
            else:
                self._append_message("Histórico", error, "error")
            if is_transcript_write:
                self._flush_transcript_queue()
            self._refresh_controls()
            return

        data = payload if isinstance(payload, dict) else {}
        if action in {"threads-list", "thread-search", "thread-search-more"}:
            threads = data.get("threads") if action == "threads-list" else data.get("results")
            if action != "thread-search-more":
                self.thread_list.clear()
            if action in {"thread-search", "thread-search-more"}:
                self._search_offset = int(data.get("next_offset") or 0)
                self._search_has_more = bool(data.get("has_more"))
            else:
                self._search_has_more = False
            for thread in threads or []:
                if not isinstance(thread, dict):
                    continue
                thread_id = thread.get("id") or thread.get("thread_id")
                title = thread.get("title") or "Nova conversa"
                if not isinstance(thread_id, str):
                    continue
                status = str(thread.get("status") or "active")
                display_title = f"{title}  [{status}]"
                item = QListWidgetItem(display_title)
                item.setData(Qt.ItemDataRole.UserRole, thread_id)
                item.setData(Qt.ItemDataRole.UserRole + 1, status)
                self.thread_list.addItem(item)
            self._refresh_controls()
            return

        if action == "thread-create":
            thread_id = data.get("id")
            if not isinstance(thread_id, str) or not thread_id:
                self._append_message("Erro", "O backend não devolveu o ID da nova conversa.", "error")
                self._pending_directive = None
                self._refresh_controls()
                return
            self._active_thread_id = thread_id
            self._active_thread_status = "active"
            self._search_has_more = False
            self.output.clear()
            self.history.clear()
            self._append_message("Sistema", "Nova conversa criada. O histórico é independente.", "system")
            self._load_threads()
            if self._pending_directive:
                self._persist_pending_user_message()
            self._refresh_controls()
            return

        if action == "send-user-entry":
            directive = self._pending_directive
            self._pending_directive = None
            if not directive:
                return
            self._append_message("Tu", directive, "user")
            self._start_request(
                directive, status_only=directive.casefold() == "runtime status"
            )
            self._flush_transcript_queue()
            return

        if action == "transcript-entry":
            self._flush_transcript_queue()
            self._refresh_controls()
            return

        if action == "thread-open":
            thread_id = data.get("id")
            messages = data.get("messages")
            if not isinstance(thread_id, str) or not isinstance(messages, list):
                self._append_message("Erro", "O backend devolveu uma conversa inválida.", "error")
                return
            self._active_thread_id = thread_id
            self._active_thread_status = str(data.get("status") or "active")
            self.output.clear()
            self.history.clear()
            for message in messages:
                if not isinstance(message, dict):
                    continue
                role = message.get("role")
                sender = "Tu" if role == "user" else "DGM-MAT" if role == "assistant" else "Sistema"
                msg_type = "user" if role == "user" else "info" if role == "assistant" else "system"
                self._append_message(sender, message.get("content", ""), msg_type)
            self._append_message("Sistema", "Conversa carregada do histórico local.", "system")
            return


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
