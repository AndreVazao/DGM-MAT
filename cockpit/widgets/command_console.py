import sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QTextEdit, QPushButton, QLabel, QListWidget
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont, QTextCursor

class CommandConsoleWidget(QWidget):
    """
    Global Cognitive Command Console - Phase 42.3-LITE.
    Allows natural language directives and runtime introspection.
    """
    def __init__(self):
        super().__init__()
        self.history = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("COGNITIVE COMMAND CONSOLE")
        header.setStyleSheet("font-weight: bold; color: #00ff00; font-size: 14px;")
        layout.addWidget(header)

        # Output area
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; font-family: 'Consolas', 'Courier New', monospace;")
        self.output.setFont(QFont("Consolas", 10))
        layout.addWidget(self.output, 1)

        # Input area
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter directive (e.g., 'Analyze all repos for tech debt')")
        self.input_field.setStyleSheet("background-color: #2d2d2d; color: #ffffff; border: 1px solid #3e3e3e; padding: 5px;")
        self.input_field.returnPressed.connect(self._handle_command)

        self.send_btn = QPushButton("EXECUTE")
        self.send_btn.setStyleSheet("background-color: #007acc; color: white; font-weight: bold; padding: 5px 15px;")
        self.send_btn.clicked.connect(self._handle_command)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)
        layout.addLayout(input_layout)

        # Initial welcome message
        self._append_output("System: Cognitive Command Console active. Awaiting directives.", "system")

    def _handle_command(self):
        cmd = self.input_field.text().strip()
        if not cmd:
            return

        self.history.append(cmd)
        self.input_field.clear()

        self._append_output(f"> {cmd}", "user")
        self._process_directive(cmd)

    def _process_directive(self, directive: str):
        """Processes the natural language directive."""
        # This will eventually call the cognitive kernel or a specialized agent
        self._append_output(f"Processing: {directive}...", "system")

        # Simulated response for Phase 42.3-LITE
        if "analyze" in directive.lower():
            self._append_output("CognitiveFS: Scanning repositories...", "info")
            self._append_output("CognitiveFS: Found 12 repos. Tech debt scan in progress.", "info")
        elif "refactor" in directive.lower():
            self._append_output("ArchitectAgent: Analyzing refactoring impact...", "info")
        else:
            self._append_output("Runtime: Dispatching directive to Cognitive Kernel.", "info")

    def _append_output(self, text: str, msg_type: str = "info"):
        color = "#d4d4d4"
        if msg_type == "user": color = "#569cd6"
        elif msg_type == "system": color = "#ce9178"
        elif msg_type == "error": color = "#f44336"

        self.output.append(f'<span style="color: {color};">{text}</span>')
        self.output.moveCursor(QTextCursor.End)

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = CommandConsoleWidget()
    window.show()
    sys.exit(app.exec())
