import sys
import requests
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QTextEdit, QPushButton, QLabel, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont, QTextCursor
from core.observability.logger import dgm_logger

class CommandConsoleWidget(QWidget):
    """
    Advanced Cognitive Chat Console - Phase 42.5.1-LITE.
    Target UX: scrolling history, streamed responses, execution state.
    Now wired to the actual Runtime API.
    """
    def __init__(self):
        super().__init__()
        self.history = []
        self.api_url = "http://localhost:8181/runtime"
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Header
        header = QLabel("COGNITIVE TERMINAL")
        header.setStyleSheet("font-weight: bold; color: #00ff00; font-size: 12px; font-family: 'Consolas';")
        layout.addWidget(header)

        # Output area (Chat History)
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(\"\"\"
            background-color: #0f0f0f;
            color: #d4d4d4;
            font-family: 'Consolas', 'Courier New', monospace;
            border: none;
            line-height: 1.4;
        \"\"\")
        self.output.setFont(QFont("Consolas", 10))
        layout.addWidget(self.output, 1)

        # Input Frame
        input_container = QFrame()
        input_container.setStyleSheet("background-color: #252526; border-top: 1px solid #3e3e3e;")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(5, 5, 5, 5)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type directive...")
        self.input_field.setStyleSheet(\"\"\"
            background-color: #3c3c3c;
            color: #ffffff;
            border: 1px solid #505050;
            padding: 8px;
            border-radius: 3px;
        \"\"\")
        self.input_field.returnPressed.connect(self._handle_command)

        self.send_btn = QPushButton("RUN")
        self.send_btn.setStyleSheet(\"\"\"
            background-color: #007acc;
            color: white;
            font-weight: bold;
            padding: 8px 20px;
            border-radius: 3px;
        \"\"\")
        self.send_btn.clicked.connect(self._handle_command)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)
        layout.addWidget(input_container)

        # Welcome message
        self._append_message("System", "Cognitive Command Console ready. Awaiting operational directives.", "system")

    def set_enabled(self, enabled: bool):
        self.input_field.setEnabled(enabled)
        self.send_btn.setEnabled(enabled)
        if not enabled:
            self.input_field.setPlaceholderText("API Offline - Input Disabled")
        else:
            self.input_field.setPlaceholderText("Type directive...")

    def _handle_command(self):
        cmd = self.input_field.text().strip()
        if not cmd:
            return

        self.input_field.clear()

        # User message
        self._append_message("You", cmd, "user")
        dgm_logger.info(f"COCKPIT_MESSAGE_RECEIVED: {cmd}")

        # Process logic
        self._process_directive(cmd)

    def _process_directive(self, directive: str):
        if directive.lower() == "runtime status":
            self._handle_runtime_status()
            return

        # Create actual mission via API
        try:
            response = requests.post(
                f"{self.api_url}/missions",
                json={"goal": directive, "description": "Directive from Cockpit Console"},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                self._append_message("Runtime", f"Mission created: {data.get('mission_id')}", "info")
            else:
                self._append_message("Error", f"Failed to create mission: {response.text}", "error")
        except Exception as e:
            self._append_message("Error", f"Communication failure: {str(e)}", "error")

    def _handle_runtime_status(self):
        """Displays comprehensive system health from Truth API."""
        try:
            response = requests.get(f"{self.api_url}/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                status_msg = (
                    f"--- RUNTIME OPERATIONAL STATUS ---\n"
                    f"Status: [{data.get('status', 'unknown').upper()}]\n"
                    f"Degraded: {data.get('is_degraded', False)}\n"
                    f"CPU: {data.get('resources', {}).get('cpu')}% | MEM: {data.get('resources', {}).get('memory')}%\n"
                    f"Active Missions: {data.get('missions_active', 0)}\n"
                    "---"
                )
                self._append_message("Status", status_msg, "system")
            else:
                self._append_message("Error", "Could not retrieve status.", "error")
        except Exception as e:
            self._append_message("Error", f"Status failure: {str(e)}", "error")

    def _append_message(self, sender: str, text: str, msg_type: str = "info"):
        ts = datetime.now().strftime("%H:%M:%S")

        colors = {
            "user": "#569cd6",    # Blue
            "system": "#ce9178",  # Orange/Brown
            "info": "#4ec9b0",    # Teal
            "error": "#f44336"    # Red
        }
        color = colors.get(msg_type, "#d4d4d4")

        html = f\"\"\"
            <div style='margin-bottom: 8px;'>
                <span style='color: #808080; font-size: 8pt;'>[{ts}]</span>
                <b style='color: {color};'>{sender}:</b>
                <div style='margin-left: 15px; color: #d4d4d4;'>{text.replace(chr(10), '<br>')}</div>
            </div>
        \"\"\"

        self.output.append(html)
        self.output.moveCursor(QTextCursor.End)
