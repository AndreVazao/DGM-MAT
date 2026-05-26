from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QLabel, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

class ChatWidget(QWidget):
    message_sent = Signal(str)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Chat history display (using QTextEdit for rich text/markdown rendering)
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setAcceptRichText(True)
        self.chat_history.setPlaceholderText("Conversation will appear here...")
        layout.addWidget(self.chat_history)

        # Input area
        input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message or command...")
        self.message_input.returnPressed.connect(self.send_message)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)

        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)
        layout.addLayout(input_layout)

    def send_message(self):
        text = self.message_input.text().strip()
        if text:
            self.append_message("User", text)
            self.message_sent.emit(text)
            self.message_input.clear()

    def append_message(self, sender: str, message: str):
        # Basic markdown/syntax highlighting logic would be integrated here
        formatted_message = f"<b>{sender}:</b> {message}<br>"
        self.chat_history.append(formatted_message)
        # Scroll to bottom
        self.chat_history.verticalScrollBar().setValue(
            self.chat_history.verticalScrollBar().maximum()
        )

    def display_streaming_chunk(self, chunk: str):
        """Used for real-time streaming display."""
        cursor = self.chat_history.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(chunk)
        self.chat_history.setTextCursor(cursor)
