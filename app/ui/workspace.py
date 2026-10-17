"""Central workspace — QStackedWidget hosting PDF / Image / Text / Quiz views.
Owns the Upload panel on the right.
"""
from __future__ import annotations
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


MODE_EMPTY = 0
MODE_PDF   = 1
MODE_IMAGE = 2
MODE_TEXT  = 3
MODE_QUIZ  = 4


class Workspace(QWidget):
    """
    Outer workspace container.
    Hosts content stack on the left and upload panel on the right.
    """

    pdfUploadRequested   = Signal()
    imageUploadRequested = Signal()
    textUploadRequested  = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("workspaceContainer")
        self.setStyleSheet("#workspaceContainer{background-color: #202A27;}")

        self._upload_visible = True
        self._prev_mode = MODE_PDF

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 12, 12)
        outer.setSpacing(12)

        # ── Content stack ──────────────────────────────────────────────────────
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("border-radius: 18px;")

        self.pdf_viewer    = PDFViewer()
        self.image_viewer  = ImageViewer()
        self.text_editor   = TextEditor()
        self.quiz_view     = QuizView()

        self._stack.addWidget(QWidget())          # 0: empty
        self._stack.addWidget(self.pdf_viewer)    # 1: pdf
        self._stack.addWidget(self.image_viewer)  # 2: image
        self._stack.addWidget(self.text_editor)   # 3: text
        self._stack.addWidget(self.quiz_view)     # 4: quiz

        outer.addWidget(self._stack, 1)

        # Drop shadow on content stack
        shadow = QGraphicsDropShadowEffect(self._stack)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 50))
        self._stack.setGraphicsEffect(shadow)

        # ── Upload panel (visible by default) ──────────────────────────────────
        self.upload_panel = UploadPanel()
        self.upload_panel.setVisible(True)
        outer.addWidget(self.upload_panel)

        # Wire upload panel
        self.upload_panel.pdfRequested.connect(self.pdfUploadRequested)
        self.upload_panel.imageRequested.connect(self.imageUploadRequested)
        self.upload_panel.textRequested.connect(self.textUploadRequested)
        self.upload_panel.closeRequested.connect(self.hide_upload_panel)

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
        self._stack.setCurrentIndex(self._prev_mode)

    def current_mode(self) -> int:
        return self._stack.currentIndex()

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
