"""Left vertical sidebar with tool buttons."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QPainterPath, QPixmap

from app.ui.icons import load_svg_pixmap


class SidebarButton(QWidget):
    """
    Vertical tool button (Icon + Text label).
    Active   → Warm yellow (#FFD04D) rounded card, dark icon & text.
    Inactive → Transparent, cream icon & text, hover darkens.
    """

    clicked = Signal()

    def __init__(self, icon_active_name: str, icon_inactive_name: str, label: str, parent=None):
        super().__init__(parent)
        self._active = False
        self._hovered = False

        self._icon_active_name   = icon_active_name
        self._icon_inactive_name = icon_inactive_name
        self._label_text         = label

        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(76, 76)
        self.setAttribute(Qt.WA_Hover, True)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 10, 0, 10)
        lay.setSpacing(6)
        lay.setAlignment(Qt.AlignCenter)

        self._icon_lbl = QLabel()
        self._icon_lbl.setAlignment(Qt.AlignCenter)
        self._icon_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self._text_lbl = QLabel(label)
        self._text_lbl.setAlignment(Qt.AlignCenter)
        self._text_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        lay.addWidget(self._icon_lbl)
        lay.addWidget(self._text_lbl)

        self._refresh()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self.rect(), 14, 14)
        if self._active:
            p.fillPath(path, QColor("#FFD04D"))
        elif self._hovered:
            p.fillPath(path, QColor("#343834"))
        p.end()

    def enterEvent(self, event):
        self._hovered = True
        self._refresh()
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self._refresh()
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

    def set_active(self, active: bool):
        self._active = active
        self._refresh()
        self.update()

    def _refresh(self):
        icon_name = self._icon_active_name if self._active else self._icon_inactive_name
        pix = load_svg_pixmap(icon_name, 26)
        self._icon_lbl.setPixmap(pix)

        if self._active:
            self._text_lbl.setStyleSheet(
                "color: #1A1C1A; font-size: 12.5px; font-weight: 700; background: transparent;"
            )
        else:
            col = "#FFFFFF" if self._hovered else "#FFF1CC"
            self._text_lbl.setStyleSheet(
                f"color: {col}; font-size: 12px; font-weight: 500; background: transparent;"
            )


class Sidebar(QWidget):
    """
    Vertical sidebar (~88 px wide):
      Top    — Select / Upload / Quiz
      Bottom — Settings / Night Mode
    """

    selectClicked   = Signal()
    uploadClicked   = Signal()
    quizClicked     = Signal()
    settingsClicked = Signal()
    themeClicked    = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(88)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("QWidget{background-color: #202A27;}")

        root = QVBoxLayout(self)
        root.setContentsMargins(6, 12, 6, 18)
        root.setSpacing(10)
        root.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        # ── Tool buttons ───────────────────────────────────────────────────────
        self.btn_select = SidebarButton(
            "select_arrow_dark.svg", "select_arrow_light.svg", "Select"
        )
        self.btn_upload = SidebarButton(
            "upload_tray.svg", "upload_tray.svg", "Upload"
        )
        self.btn_quiz = SidebarButton(
            "quiz_badge.svg", "quiz_badge.svg", "Quiz"
        )

        root.addWidget(self.btn_select, 0, Qt.AlignHCenter)
        root.addWidget(self.btn_upload, 0, Qt.AlignHCenter)
        root.addWidget(self.btn_quiz,   0, Qt.AlignHCenter)

        root.addStretch(1)

        # ── Bottom buttons (Settings & Theme) ──────────────────────────────────
        self.btn_settings = self._bottom_btn("settings_gear.svg", "Settings")
        self.btn_theme    = self._bottom_btn("moon_crescent.svg", "Toggle Night Mode")

        root.addWidget(self.btn_settings, 0, Qt.AlignHCenter)
        root.addSpacing(6)
        root.addWidget(self.btn_theme,    0, Qt.AlignHCenter)

        # ── Signal wiring ──────────────────────────────────────────────────────
        self.btn_select.clicked.connect(self._on_select)
        self.btn_upload.clicked.connect(self._on_upload)
        self.btn_quiz.clicked.connect(self._on_quiz)
        self.btn_settings.clicked.connect(self.settingsClicked)
        self.btn_theme.clicked.connect(self.themeClicked)

        self._active_tool = "select"
        self.btn_select.set_active(True)

    def _bottom_btn(self, icon_name: str, tip: str) -> QPushButton:
        b = QPushButton()
        b.setFixedSize(38, 38)
        b.setCursor(Qt.PointingHandCursor)
        b.setToolTip(tip)
        pix = load_svg_pixmap(icon_name, 22)
        b.setIcon(pix)
        b.setIconSize(pix.size())
        b.setStyleSheet(
            "QPushButton{"
            "background: transparent;"
            "border-radius: 10px;"
            "border: none;"
            "}"
            "QPushButton:hover{background-color: #343834;}"
        )
        return b

    def _set_active(self, name: str):
        self._active_tool = name
        self.btn_select.set_active(name == "select")
        self.btn_upload.set_active(name == "upload")
        self.btn_quiz.set_active(name == "quiz")

    def _on_select(self):
        self._set_active("select")
        self.selectClicked.emit()

    def _on_upload(self):
        self.uploadClicked.emit()

    def _on_quiz(self):
        self._set_active("quiz")
        self.quizClicked.emit()

    def set_active_tool(self, name: str):
        self._set_active(name)
