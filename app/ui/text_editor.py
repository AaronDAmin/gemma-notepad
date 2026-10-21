"""Rich study notes dashboard — rich-text editor with formatting toolbar."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel,
    QComboBox, QFrame, QScrollArea, QLineEdit, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (
    QFont, QTextCharFormat, QTextCursor, QTextListFormat,
    QColor, QTextBlockFormat
)

from app.ui.icons import load_svg_pixmap


class TextEditor(QWidget):
    """
    Rich study notes dashboard.
    Supports rich text formatting (bold, italic, underline, strike, headings, lists, code),
    editable note title, and selection-triggered AI explanations.
    """

    textSelected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("textEditor")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(
            "#textEditor{background-color: #FFF8EC; border-radius: 18px;}"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Formatting Toolbar ─────────────────────────────────────────────────
        toolbar = QWidget()
        toolbar.setFixedHeight(48)
        toolbar.setStyleSheet(
            "background-color: #FFF8EC; border-bottom: 1px solid #EDD89A;"
            "border-top-left-radius: 18px; border-top-right-radius: 18px;"
        )
        t_lay = QHBoxLayout(toolbar)
        t_lay.setContentsMargins(18, 0, 18, 0)
        t_lay.setSpacing(6)

        # Doc icon
        doc_box = QFrame()
        doc_box.setFixedSize(28, 28)
        doc_box.setStyleSheet("background-color: #F6ECCF; border-radius: 6px;")
        db_lay = QVBoxLayout(doc_box)
        db_lay.setContentsMargins(0, 0, 0, 0)
        db_lay.setAlignment(Qt.AlignCenter)
        db_lbl = QLabel()
        db_lbl.setPixmap(load_svg_pixmap("text_card_icon.svg", 16, color="#1A1C1A"))
        db_lay.addWidget(db_lbl)
        t_lay.addWidget(doc_box)

        # Style format combo (Normal / H1 / H2 / H3 / Code)
        self.combo_format = QComboBox()
        self.combo_format.setFixedSize(115, 28)
        self.combo_format.setStyleSheet(
            "QComboBox{background-color: #F6ECCF; border: 1px solid #E8DCB8; border-radius: 6px;"
            "color: #1A1C1A; font-size: 12px; font-weight: 500; padding-left: 6px;}"
            "QComboBox::drop-down{border: none; width: 18px;}"
            "QComboBox QAbstractItemView{background-color: #FFF8EC; color: #1A1C1A;"
            "selection-background-color: #FFD04D; selection-color: #1A1C1A;}"
        )
        self.combo_format.addItems(["Normal Text", "Heading 1", "Heading 2", "Heading 3", "Code Block"])
        self.combo_format.currentIndexChanged.connect(self._on_format_changed)
        t_lay.addWidget(self.combo_format)

        t_lay.addWidget(self._separator())

        # Inline format buttons
        self.btn_bold      = self._tool_btn("B", "Bold (Ctrl+B)", bold=True)
        self.btn_italic    = self._tool_btn("I", "Italic (Ctrl+I)", italic=True)
        self.btn_underline = self._tool_btn("U", "Underline (Ctrl+U)", underline=True)
        self.btn_strike    = self._tool_btn("S̶", "Strikethrough")

        t_lay.addWidget(self.btn_bold)
        t_lay.addWidget(self.btn_italic)
        t_lay.addWidget(self.btn_underline)
        t_lay.addWidget(self.btn_strike)

        t_lay.addWidget(self._separator())

        # List buttons
        self.btn_bullet = self._tool_btn("•", "Bullet list")
        self.btn_number = self._tool_btn("1.", "Numbered list")
        t_lay.addWidget(self.btn_bullet)
        t_lay.addWidget(self.btn_number)

        t_lay.addWidget(self._separator())

        self.btn_code = self._tool_btn("< >", "Code block")
        t_lay.addWidget(self.btn_code)

        t_lay.addStretch(1)

        # Save action
        self.btn_save = QPushButton("Save")
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setStyleSheet(
            "QPushButton{background-color: #FFD04D; border-radius: 8px; color: #1A1C1A;"
            "font-size: 13px; font-weight: 700; padding: 5px 18px; border: none;}"
            "QPushButton:hover{background-color: #E8B93A;}"
            "QPushButton:pressed{background-color: #D4A017;}"
        )
        t_lay.addWidget(self.btn_save)

        root.addWidget(toolbar)

        # ── Writing Surface Container ──────────────────────────────────────────
        canvas_container = QWidget()
        canvas_container.setStyleSheet(
            "background-color: #FCF6EC;"
            "border-bottom-left-radius: 18px; border-bottom-right-radius: 18px;"
        )
        c_lay = QVBoxLayout(canvas_container)
        c_lay.setContentsMargins(40, 24, 40, 24)
        c_lay.setSpacing(12)

        # Title Input
        self.title_input = QLineEdit("Notes - Normalization")
        self.title_input.setStyleSheet(
            "QLineEdit{background: transparent; border: none; color: #1A1C1A;"
            "font-size: 24px; font-weight: 800; font-family: 'Segoe UI', sans-serif;}"
            "QLineEdit:focus{border-bottom: 2px solid #FFD04D;}"
        )
        c_lay.addWidget(self.title_input)

        # Rich Editor
        self.editor = QTextEdit()
        self.editor.setStyleSheet(
            "QTextEdit{"
            "background-color: #FCF6EC; border: none; color: #1A1C1A;"
            "font-size: 15px; font-family: 'Segoe UI', sans-serif; line-height: 1.6;"
            "selection-background-color: #FFD04D; selection-color: #1A1C1A;"
            "}"
        )
        self.editor.setPlaceholderText("Start typing your study notes here… Highlight text to explain with AI.")
        self.editor.selectionChanged.connect(self._on_selection)
        c_lay.addWidget(self.editor, 1)

        root.addWidget(canvas_container, 1)

        # ── Signal wiring ──────────────────────────────────────────────────────
        self.btn_bold.clicked.connect(self._toggle_bold)
        self.btn_italic.clicked.connect(self._toggle_italic)
        self.btn_underline.clicked.connect(self._toggle_underline)
        self.btn_strike.clicked.connect(self._toggle_strike)
        self.btn_bullet.clicked.connect(self._insert_bullet_list)
        self.btn_number.clicked.connect(self._insert_number_list)
        self.btn_code.clicked.connect(self._insert_code)

    def _separator(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedWidth(1)
        sep.setFixedHeight(18)
        sep.setStyleSheet("background-color: #EDD89A;")
        return sep

    def _tool_btn(self, text: str, tip: str, bold: bool = False,
                  italic: bool = False, underline: bool = False) -> QPushButton:
        b = QPushButton(text)
        b.setFixedSize(28, 28)
        b.setCursor(Qt.PointingHandCursor)
        b.setToolTip(tip)
        font_weight = "700" if bold else "500"
        font_style = "italic" if italic else "normal"
        text_decor = "underline" if underline else "none"
        b.setStyleSheet(
            f"QPushButton{{background-color: transparent; border: none; border-radius: 6px;"
            f"color: #1A1C1A; font-size: 13.5px; font-weight: {font_weight};"
            f"font-style: {font_style}; text-decoration: {text_decor};}}"
            f"QPushButton:hover{{background-color: #EEDBBA;}}"
            f"QPushButton:pressed{{background-color: #DDC8A0;}}"
        )
        return b

    # ── Formatting Actions ─────────────────────────────────────────────────────

    def _toggle_bold(self):
        fmt = self.editor.currentCharFormat()
        weight = QFont.Normal if fmt.fontWeight() == QFont.Bold else QFont.Bold
        fmt.setFontWeight(weight)
        self.editor.mergeCurrentCharFormat(fmt)

    def _toggle_italic(self):
        fmt = self.editor.currentCharFormat()
        fmt.setFontItalic(not fmt.fontItalic())
        self.editor.mergeCurrentCharFormat(fmt)

    def _toggle_underline(self):
        fmt = self.editor.currentCharFormat()
        fmt.setFontUnderline(not fmt.fontUnderline())
        self.editor.mergeCurrentCharFormat(fmt)

    def _toggle_strike(self):
        fmt = self.editor.currentCharFormat()
        fmt.setFontStrikeOut(not fmt.fontStrikeOut())
        self.editor.mergeCurrentCharFormat(fmt)

    def _on_format_changed(self, idx: int):
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        fmt = QTextCharFormat()

        if idx == 0:  # Normal Text
            fmt.setFontPointSize(15)
            fmt.setFontWeight(QFont.Normal)
            fmt.setFontFamilies(["Segoe UI"])
        elif idx == 1:  # H1
            fmt.setFontPointSize(22)
            fmt.setFontWeight(QFont.Bold)
            fmt.setFontFamilies(["Segoe UI"])
        elif idx == 2:  # H2
            fmt.setFontPointSize(18)
            fmt.setFontWeight(QFont.Bold)
            fmt.setFontFamilies(["Segoe UI"])
        elif idx == 3:  # H3
            fmt.setFontPointSize(16)
            fmt.setFontWeight(QFont.Bold)
            fmt.setFontFamilies(["Segoe UI"])
        elif idx == 4:  # Code
            fmt.setFontPointSize(13.5)
            fmt.setFontWeight(QFont.Normal)
            fmt.setFontFamilies(["Consolas"])

        cursor.mergeCharFormat(fmt)
        cursor.endEditBlock()
        self.editor.setCurrentCharFormat(fmt)

    def _insert_bullet_list(self):
        cursor = self.editor.textCursor()
        cursor.insertList(QTextListFormat.ListDisc)

    def _insert_number_list(self):
        cursor = self.editor.textCursor()
        cursor.insertList(QTextListFormat.ListDecimal)

    def _insert_code(self):
        cursor = self.editor.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontFamilies(["Consolas"])
        fmt.setFontPointSize(13)
        fmt.setBackground(QColor("#EADBBA"))
        cursor.insertText(" `code` ", fmt)

    def _on_selection(self):
        text = self.editor.textCursor().selectedText().strip()
        if text:
            self.textSelected.emit(text)

    # ── Public API ─────────────────────────────────────────────────────────────

    def get_content(self) -> str:
        return self.editor.toPlainText()

    def set_content(self, text: str):
        self.editor.setPlainText(text)

    def set_title(self, title: str):
        self.title_input.setText(title)

    def get_title(self) -> str:
        return self.title_input.text().strip()
