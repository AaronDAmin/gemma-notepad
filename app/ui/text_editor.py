"""Plain-text note editor widget."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QPlainTextEdit, QLabel
)
from PySide6.QtCore import Qt, Signal


class TextEditor(QWidget):
    """
    Minimal plain-text editor.
    Emits textSelected(str) when the user selects text (AI popup — Phase 3).
    """

    textSelected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("workspacePanel")
        self.setStyleSheet(
            "QWidget#workspacePanel{background:#FFF8EC;border-radius:16px;}"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Toolbar ────────────────────────────────────────────────────────────
        toolbar = QWidget()
        toolbar.setFixedHeight(48)
        toolbar.setStyleSheet(
            "background:#FFF8EC;"
            "border-bottom:1px solid #EDD89A;"
            "border-top-left-radius:16px;"
            "border-top-right-radius:16px;"
        )
        t_lay = QHBoxLayout(toolbar)
        t_lay.setContentsMargins(14, 0, 14, 0)

        note_lbl = QLabel("Notes")
        note_lbl.setStyleSheet(
            "color:#4A4E4A;font-size:14px;font-weight:600;"
            "background:transparent;"
        )

        self.btn_save = QPushButton("Save")
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setStyleSheet(
            "QPushButton{background:#F0C94C;border-radius:8px;color:#1A1C1A;"
            "font-size:13px;font-weight:600;padding:5px 18px;border:none;}"
            "QPushButton:hover{background:#E8B93A;}"
            "QPushButton:pressed{background:#D4A017;}"
        )

        t_lay.addWidget(note_lbl)
        t_lay.addStretch()
        t_lay.addWidget(self.btn_save)
        root.addWidget(toolbar)

        # ── Editor ─────────────────────────────────────────────────────────────
        self.editor = QPlainTextEdit()
        self.editor.setStyleSheet(
            "QPlainTextEdit{"
            "background:#FFF8EC;border:none;color:#1A1C1A;"
            "font-size:14px;font-family:'Segoe UI',sans-serif;"
            "padding:20px 30px;"
            "border-bottom-left-radius:16px;"
            "border-bottom-right-radius:16px;"
            "selection-background-color:#F0C94C;"
            "selection-color:#1A1C1A;"
            "}"
        )
        self.editor.setPlaceholderText("Start typing your notes here…")
        self.editor.selectionChanged.connect(self._on_selection)
        root.addWidget(self.editor, 1)

    def _on_selection(self):
        text = self.editor.textCursor().selectedText().strip()
        if text:
            self.textSelected.emit(text)

    # ── Public API ─────────────────────────────────────────────────────────────

    def get_content(self) -> str:
        return self.editor.toPlainText()

    def set_content(self, text: str):
        self.editor.setPlainText(text)
