"""Left vertical sidebar with tool buttons."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFrame, QLabel,
    QSizePolicy, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QPainterPath


class SidebarButton(QWidget):
    """
    Icon + label button that paints itself directly.
    Active → GemmaNotepad1 #F0C94C rounded card.
    Inactive → transparent, greyed icons, hover darkens.
    """

    clicked = Signal()

    def __init__(self, icon_text: str, label: str, parent=None):
        super().__init__(parent)
        self._active  = False
        self._hovered = False

        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(80, 90)
        self.setAttribute(Qt.WA_Hover, True)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 8, 0, 8)
        lay.setSpacing(2)
        lay.setAlignment(Qt.AlignCenter)

        self._icon = QLabel(icon_text)
        self._icon.setAlignment(Qt.AlignCenter)
        self._icon.setFixedHeight(26)
        self._icon.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self._text = QLabel(label)
        self._text.setAlignment(Qt.AlignCenter)
        self._text.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        lay.addWidget(self._icon)
        lay.addWidget(self._text)

        self._refresh()

    # ── Paint background ───────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        if self._active:
            path = QPainterPath()
            path.addRoundedRect(self.rect(), 12, 12)
            p.fillPath(path, QColor("#F0C94C"))
        elif self._hovered:
            path = QPainterPath()
            path.addRoundedRect(self.rect(), 12, 12)
            p.fillPath(path, QColor("#343834"))
        p.end()

    # ── Events ────────────────────────────────────────────────────────────────

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

    # ── State ─────────────────────────────────────────────────────────────────

    def set_active(self, active: bool):
        self._active = active
        self._refresh()
        self.update()

    def _refresh(self):
        """Update child label styles based on current state."""
        if self._active:
            self._icon.setStyleSheet(
                "background:transparent;font-size:22px;color:#1A1C1A;"
            )
            self._text.setStyleSheet(
                "background:transparent;font-size:14px;"
                "font-weight:700;color:#1A1C1A;"
            )
        else:
            text_col = "#C0C8C0" if self._hovered else "#FFF1CC"
            self._icon.setStyleSheet(
                f"background:transparent;font-size:22px;color:{text_col};"
            )
            self._text.setStyleSheet(
                f"background:transparent;font-size:14px;"
                f"font-weight:500;color:{text_col};"
            )


class Sidebar(QWidget):
    """
    Vertical sidebar (78 px wide):
      Top    — Select / Upload / Quiz
      Bottom — Settings / Theme
    """

    selectClicked   = Signal()
    uploadClicked   = Signal()
    quizClicked     = Signal()
    settingsClicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(104)
        # Paint background explicitly so it isn't transparent
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("QWidget{background:#202A27;}")

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 0, 12, 20)
        root.setSpacing(14)
        root.setAlignment(Qt.AlignTop)

        # Tool buttons — use a cursor icon from unicode for Select
        self.btn_select = SidebarButton("↖", "Select")
        self.btn_upload = SidebarButton("↑", "Upload")
        self.btn_quiz   = SidebarButton("?", "Quiz")

        root.addWidget(self.btn_select, 0, Qt.AlignHCenter)
        root.addSpacing(4)
        root.addWidget(self.btn_upload, 0, Qt.AlignHCenter)
        root.addSpacing(4)
        root.addWidget(self.btn_quiz,   0, Qt.AlignHCenter)

        root.addStretch()

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background:#3D413D;")
        root.addWidget(sep)
        root.addSpacing(10)

        # Bottom buttons
        self.btn_settings = self._bottom_btn("⚙", "Settings")

        root.addWidget(self.btn_settings, 0, Qt.AlignHCenter)

        # Wire
        self.btn_select.clicked.connect(self._on_select)
        self.btn_upload.clicked.connect(self._on_upload)
        self.btn_quiz.clicked.connect(self._on_quiz)
        self.btn_settings.clicked.connect(self.settingsClicked)

        self._active_tool = "select"
        self.btn_select.set_active(True)

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _bottom_btn(self, icon: str, tip: str) -> QPushButton:
        b = QPushButton(icon)
        b.setFixedSize(38, 38)
        b.setCursor(Qt.PointingHandCursor)
        b.setToolTip(tip)
        b.setStyleSheet(
            "QPushButton{background:transparent;border-radius:10px;"
            "color:#FFF1CC;font-size:18px;border:none;}"
            "QPushButton:hover{background:#343834;color:#B0B8B0;}"
        )
        return b

    # ── Internal ───────────────────────────────────────────────────────────────

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

    # ── Public API ─────────────────────────────────────────────────────────────

    def set_active_tool(self, name: str):
        self._set_active(name)
