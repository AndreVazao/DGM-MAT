"""Chat-first desktop cockpit with a persistent, searchable conversation sidebar."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from cockpit.widgets.command_console import CommandConsoleWidget


class MinimalChatWindow(QMainWindow):
    """Present DGM-MAT as a familiar chat, not as an operator control panel."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DGM-MAT — Assistente")
        self.resize(1180, 780)
        self.setMinimumSize(760, 560)

        self.chat = CommandConsoleWidget()
        self._build_chat_first_layout()
        self.statusBar().showMessage("DGM-MAT | Ligação local")

    def _build_chat_first_layout(self) -> None:
        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("conversationSidebar")
        sidebar.setFixedWidth(270)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 20, 16, 16)
        sidebar_layout.setSpacing(12)

        brand = QLabel("∿  DGM-MAT")
        brand.setObjectName("sidebarBrand")
        sidebar_layout.addWidget(brand)

        subtitle = QLabel("O teu escritório inteligente")
        subtitle.setObjectName("sidebarSubtitle")
        sidebar_layout.addWidget(subtitle)

        new_chat = QPushButton("＋  Nova conversa")
        new_chat.setObjectName("primarySidebarButton")
        new_chat.setCursor(Qt.CursorShape.PointingHandCursor)
        new_chat.clicked.connect(self.chat._create_thread)
        sidebar_layout.addWidget(new_chat)

        search_label = QLabel("HISTÓRICO")
        search_label.setObjectName("sidebarSectionLabel")
        sidebar_layout.addWidget(search_label)

        search = QLineEdit()
        search.setObjectName("conversationSearch")
        search.setPlaceholderText("Pesquisar conversas…")
        search.returnPressed.connect(self.chat._search_threads)
        sidebar_layout.addWidget(search)

        # Reuse the existing authenticated, paginated history list and its handlers.
        chat_layout = self.chat.layout()
        self._legacy_sidebar_controls = []
        for widget in (
            self.chat.new_thread_btn,
            self.chat.search_field,
            self.chat.search_btn,
            self.chat.ai_help_btn,
            self.chat.search_more_btn,
            self.chat.archive_thread_btn,
        ):
            widget.hide()
            widget.setParent(None)
            self._legacy_sidebar_controls.append(widget)

        header = chat_layout.itemAt(0).widget()
        history_bar = chat_layout.itemAt(1).layout()
        if header:
            header.hide()
        if history_bar:
            history_bar.setEnabled(False)
        chat_layout.removeWidget(self.chat.thread_list)
        self.chat.thread_list.setParent(sidebar)
        self.chat.thread_list.setMaximumHeight(16777215)
        self.chat.thread_list.setMinimumHeight(160)
        self.chat.thread_list.setObjectName("conversationHistory")
        sidebar_layout.addWidget(self.chat.thread_list, 1)

        # Existing handlers continue to own search, pagination and archive state.
        self.chat.search_field = search
        self.chat.new_thread_btn = new_chat

        more = QPushButton("Mais conversas")
        more.setObjectName("sidebarSecondaryButton")
        more.setEnabled(False)
        more.clicked.connect(self.chat._search_more_threads)
        sidebar_layout.addWidget(more)
        self.chat.search_more_btn = more

        archive = QPushButton("Arquivar / restaurar")
        archive.setObjectName("sidebarSecondaryButton")
        archive.clicked.connect(self.chat._archive_selected_thread)
        sidebar_layout.addWidget(archive)
        self.chat.archive_thread_btn = archive

        help_ai = QPushButton("Pedir ajuda a uma IA")
        help_ai.setObjectName("sidebarSecondaryButton")
        help_ai.clicked.connect(self.chat._open_ai_consultation)
        sidebar_layout.addWidget(help_ai)
        self.chat.ai_help_btn = help_ai

        status = QPushButton("Ver estado do sistema")
        status.setObjectName("sidebarTextButton")
        status.clicked.connect(self.chat._handle_runtime_status)
        sidebar_layout.addWidget(status)

        footer = QLabel("LOCAL  •  DADOS NO TEU PC")
        footer.setObjectName("sidebarFooter")
        sidebar_layout.addWidget(footer)

        root.addWidget(sidebar)
        self.chat.setParent(central)
        root.addWidget(self.chat, 1)
        self.setCentralWidget(central)

        # Keep the sidebar controls in sync with the same state machine as the chat.
        self.chat.thread_list.itemSelectionChanged.connect(self.chat._refresh_controls)
        self.chat._refresh_controls()
