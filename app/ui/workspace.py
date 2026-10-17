"""Central workspace — QStackedWidget that hosts PDF / Image / Text / Quiz views.
Also owns the Upload panel overlay.
"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget, QLabel,
    QPushButton, QSizePolicy, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from app.ui.pdf_viewer    import PDFViewer
from app.ui.image_viewer  import ImageViewer
from app.ui.text_editor   import TextEditor
from app.ui.quiz_view     import QuizView
from app.ui.upload_dialog import UploadPanel
from app.ui.ai_popup      import AIContextPopup


# Content mode indices inside the stacked widget
MODE_EMPTY = 0
MODE_PDF   = 1
MODE_IMAGE = 2
MODE_TEXT  = 3
MODE_QUIZ  = 4


class EmptyState(QWidget):
    """Shown when no document is open in the current workspace."""

    uploadRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("workspacePanel")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)

        icon = QLabel("📚")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size:52px; background:transparent;")

        title = QLabel("No document open")
        title.setObjectName("emptyStateTitle")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "color:#D4A017; font-size:22px; font-weight:700; background:transparent;"
        )

        subtitle = QLabel(
            "Upload a PDF, image, or start a new text note\nto begin studying."
        )
        subtitle.setObjectName("emptyStateSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(
            "color:#8A9A8A; font-size:14px; background:transparent;"
        )

        btn = QPushButton("⬆  Upload Content")
        btn.setObjectName("emptyStateBtn")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            "QPushButton{background:#F0C94C;border-radius:10px;color:#1A1C1A;"
            "font-size:14px;font-weight:600;padding:12px 28px;}"
            "QPushButton:hover{background:#E8B93A;}"
        )
        btn.clicked.connect(self.uploadRequested)

        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(8)
        layout.addWidget(btn, 0, Qt.AlignHCenter)


class Workspace(QWidget):
    """
    Outer workspace container.
    Hosts the content stack on the left and the upload panel (toggleable) on the right.
    """

    # Forwarded signals
    pdfUploadRequested   = Signal()
    imageUploadRequested = Signal()
    textUploadRequested  = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("workspaceContainer")
        self.setStyleSheet("#workspaceContainer{background:#282B28; padding:12px 12px 12px 8px;}")

        self._upload_visible = False
        self._prev_mode = MODE_EMPTY

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(12)

        # ── Content stack ──────────────────────────────────────────────────────
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("border-radius:16px;")

        self._empty_state  = EmptyState()
        self.pdf_viewer    = PDFViewer()
        self.image_viewer  = ImageViewer()
        self.text_editor   = TextEditor()
        self.quiz_view     = QuizView()

        self._stack.addWidget(self._empty_state)   # 0
        self._stack.addWidget(self.pdf_viewer)     # 1
        self._stack.addWidget(self.image_viewer)   # 2
        self._stack.addWidget(self.text_editor)    # 3
        self._stack.addWidget(self.quiz_view)      # 4

        outer.addWidget(self._stack, 1)

        # Drop shadow on the content panel
        shadow = QGraphicsDropShadowEffect(self._stack)
        shadow.setBlurRadius(32)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 90))
        self._stack.setGraphicsEffect(shadow)

        # ── Upload panel (hidden by default) ───────────────────────────────────
        self.upload_panel = UploadPanel()
        self.upload_panel.setVisible(False)
        outer.addWidget(self.upload_panel, 0, Qt.AlignTop)

        # ── AI context popup (floats over workspace) ───────────────────────────
        self.ai_popup = AIContextPopup(self)
        self.ai_popup.hide()

        # Wire upload panel signals
        self.upload_panel.pdfRequested.connect(self.pdfUploadRequested)
        self.upload_panel.imageRequested.connect(self.imageUploadRequested)
        self.upload_panel.textRequested.connect(self.textUploadRequested)
        self.upload_panel.closeRequested.connect(self.hide_upload_panel)

        # Empty state upload shortcut
        self._empty_state.uploadRequested.connect(self.toggle_upload_panel)

    # ── Mode switching ─────────────────────────────────────────────────────────

    def show_empty(self):
        self._stack.setCurrentIndex(MODE_EMPTY)

    def show_pdf(self):
        self._stack.setCurrentIndex(MODE_PDF)

    def show_image(self):
        self._stack.setCurrentIndex(MODE_IMAGE)

    def show_text(self):
        self._stack.setCurrentIndex(MODE_TEXT)

    def show_quiz(self):
        self._prev_mode = self._stack.currentIndex()
        self._stack.setCurrentIndex(MODE_QUIZ)

    def return_from_quiz(self):
        """Go back to whatever was shown before quiz."""
        self._stack.setCurrentIndex(self._prev_mode)

    def current_mode(self) -> int:
        return self._stack.currentIndex()

    # ── Upload panel ───────────────────────────────────────────────────────────

    def toggle_upload_panel(self):
        if self._upload_visible:
            self.hide_upload_panel()
        else:
            self.show_upload_panel()

    def show_upload_panel(self):
        self._upload_visible = True
        self.upload_panel.setVisible(True)

    def hide_upload_panel(self):
        self._upload_visible = False
        self.upload_panel.setVisible(False)

    def is_upload_visible(self) -> bool:
        return self._upload_visible
