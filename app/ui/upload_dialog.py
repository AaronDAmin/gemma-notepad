"""Upload panel — floats on the right of the workspace."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QSizePolicy, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath


class UploadOptionCard(QWidget):
    """One upload type row (PDF / Image / Text)."""

    clicked = Signal()

    # bg_color: card background; icon_bg: icon circle background
    def __init__(self, icon: str, title: str, desc: str,
                 bg_color: str = "#F7E7B5", icon_bg: str = "rgba(0,0,0,0.10)",
                 parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._bg   = bg_color
        self._hover = self._darken(bg_color)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(12)

        # Icon square
        icon_box = QFrame()
        icon_box.setFixedSize(48, 48)
        icon_box.setStyleSheet(
            f"background:{icon_bg}; border-radius:8px;"
        )
        icon_lbl = QLabel(icon, icon_box)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setGeometry(0, 0, 48, 48)
        icon_lbl.setStyleSheet("background:transparent; font-size:24px;color:#15201D;")

        # Text
        text_w = QWidget()
        text_w.setStyleSheet("background:transparent;")
        text_l = QVBoxLayout(text_w)
        text_l.setContentsMargins(0, 0, 0, 0)
        text_l.setSpacing(1)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(
            "background:transparent;font-size:16px;font-weight:600;color:#1A1C1A;"
        )
        lbl_desc = QLabel(desc)
        lbl_desc.setStyleSheet(
            "background:transparent;font-size:12px;color:#4A4E4A;"
        )
        text_l.addWidget(lbl_title)
        text_l.addWidget(lbl_desc)

        arrow = QLabel("›")
        arrow.setStyleSheet(
            "background:transparent;font-size:20px;color:#4A4E4A;"
        )

        lay.addWidget(icon_box)
        lay.addWidget(text_w, 1)
        lay.addWidget(arrow)

        for child in self.findChildren(QWidget):
            child.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self._pressed = False
        self._hovered = False
        self._apply_style(False)

    def _darken(self, hex_color: str) -> str:
        mapping = {
            "#F0C94C": "#E8B93A",
            "#F7E7B5": "#EDD89A",
        }
        return mapping.get(hex_color, hex_color)

    def _apply_style(self, hovered: bool):
        bg = self._hover if hovered else self._bg
        self.setStyleSheet(
            f"QWidget{{background:{bg};border-radius:12px;}}"
        )

    def enterEvent(self, e):
        self._apply_style(True)

    def leaveEvent(self, e):
        self._apply_style(False)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit()


class RecentItem(QWidget):
    """One row in the Recent Uploads list."""

    clicked = Signal()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit()

    def __init__(self, icon: str, name: str, meta: str,
                 badge_color: str = "#F0C94C", parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(68)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 6, 4, 6)
        lay.setSpacing(10)

        # Coloured badge
        badge = QFrame()
        badge.setFixedSize(32, 32)
        badge.setStyleSheet(
            f"background:{badge_color};border-radius:6px;"
        )
        badge_lbl = QLabel(icon, badge)
        badge_lbl.setAlignment(Qt.AlignCenter)
        badge_lbl.setGeometry(0, 0, 32, 32)
        badge_lbl.setStyleSheet("background:transparent;font-size:13px;")

        # Text
        text_w = QWidget()
        text_w.setStyleSheet("background:transparent;")
        text_l = QVBoxLayout(text_w)
        text_l.setContentsMargins(0, 0, 0, 0)
        text_l.setSpacing(1)

        lbl_name = QLabel(name)
        lbl_name.setStyleSheet(
            "background:transparent;font-size:13px;font-weight:500;color:#1A1C1A;"
        )
        lbl_name.setMaximumWidth(225)
        lbl_name.setToolTip(name)

        lbl_meta = QLabel(meta)
        lbl_meta.setStyleSheet(
            "background:transparent;font-size:12px;color:#8A9A8A;"
        )
        text_l.addWidget(lbl_name)
        text_l.addWidget(lbl_meta)

        menu_btn = QPushButton("⋮")
        menu_btn.setFixedSize(22, 22)
        menu_btn.setCursor(Qt.PointingHandCursor)
        menu_btn.setStyleSheet(
            "QPushButton{background:transparent;color:#8A9A8A;"
            "font-size:16px;border:none;border-radius:4px;}"
            "QPushButton:hover{background:#EDD89A;}"
        )

        lay.addWidget(badge)
        lay.addWidget(text_w, 1)
        lay.addWidget(menu_btn)

        for child in self.findChildren(QWidget):
            child.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._hovered = False

    def enterEvent(self, e):
        self.setStyleSheet("QWidget{background:#F7E7B5;border-radius:8px;}")

    def leaveEvent(self, e):
        self.setStyleSheet("")


class UploadPanel(QWidget):
    """
    Cream-coloured panel that slides in on the right.
    Fixed width of 280px to avoid overflowing small windows.
    """

    documentRequested = Signal(int)
    pdfRequested   = Signal()
    imageRequested = Signal()
    textRequested  = Signal()
    closeRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(350)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(-4, 0)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(shadow)

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 22, 22, 22)
        root.setSpacing(0)

        # ── Header ─────────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        hdr.setSpacing(0)

        title_col = QVBoxLayout()
        title_col.setSpacing(18)

        lbl_title = QLabel("Upload Content")
        lbl_title.setStyleSheet(
            "color:#1A1C1A;font-size:22px;font-weight:700;background:transparent;"
        )

        lbl_sub = QLabel("Choose what you want to add\nto your document:")
        lbl_sub.setStyleSheet(
            "color:#4A4E4A;font-size:12px;background:transparent;"
        )
        lbl_sub.setWordWrap(True)

        title_col.addWidget(lbl_title)
        title_col.addWidget(lbl_sub)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(26, 26)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(
            "QPushButton{background:transparent;border-radius:7px;"
            "color:#8A9A8A;font-size:16px;border:none;}"
            "QPushButton:hover{background:#EDD89A;color:#1A1C1A;}"
        )
        close_btn.clicked.connect(self.closeRequested)

        hdr.addLayout(title_col, 1)
        hdr.addWidget(close_btn, 0, Qt.AlignTop)
        root.addLayout(hdr)
        root.addSpacing(14)

        # ── Option cards ───────────────────────────────────────────────────────
        self.card_pdf = UploadOptionCard(
            "📄", "PDF", "Import and view a PDF document",
            bg_color="#F0C94C", icon_bg="rgba(0,0,0,0.12)"
        )
        self.card_img = UploadOptionCard(
            "🖼", "Image", "Add an image (PNG, JPG, etc.)",
            bg_color="#F7E7B5", icon_bg="#EDD89A"
        )
        self.card_txt = UploadOptionCard(
            "📝", "Text", "Create a new text document",
            bg_color="#F7E7B5", icon_bg="#EDD89A"
        )

        self.card_pdf.clicked.connect(self.pdfRequested)
        self.card_img.clicked.connect(self.imageRequested)
        self.card_txt.clicked.connect(self.textRequested)

        root.addWidget(self.card_pdf)
        root.addSpacing(14)
        root.addWidget(self.card_img)
        root.addSpacing(14)
        root.addWidget(self.card_txt)
        root.addSpacing(24)

        # ── Recent uploads ─────────────────────────────────────────────────────
        recent_hdr = QHBoxLayout()
        lbl_recent = QLabel("Recent Uploads")
        lbl_recent.setStyleSheet(
            "color:#1A1C1A;font-size:22px;font-weight:700;background:transparent;"
        )
        btn_see = QPushButton("Recent")
        btn_see.setEnabled(False)
        btn_see.setCursor(Qt.PointingHandCursor)
        btn_see.setStyleSheet(
            "QPushButton{background:transparent;color:#D4A017;"
            "font-size:13px;font-weight:600;border:none;}"
            "QPushButton:hover{color:#F0C94C;}"
        )
        recent_hdr.addWidget(lbl_recent)
        recent_hdr.addStretch()
        recent_hdr.addWidget(btn_see)
        root.addLayout(recent_hdr)
        root.addSpacing(6)

        # Items with distinct badge colours (red, green, grey like reference)
        self._items = []
        for item in self._items:
            root.addWidget(item)

        root.addStretch()

    # ── Paint cream background with rounded corners ────────────────────────────
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self.rect(), 16, 16)
        p.fillPath(path, QColor("#FCF1D8"))
        p.end()

    # ── Public API ─────────────────────────────────────────────────────────────

    def refresh_recent(self, items: list[tuple[str, str, str, int]]):
        """
        Refresh the recent items list.
        items: list of (icon, name, meta) tuples.
        """
        # Remove old items
        for item in self._items:
            self.layout().removeWidget(item)
            item.deleteLater()
        self._items.clear()

        badge_colors = {"📄": "#E05555", "🖼": "#4CAF82", "📝": "#8A9A8A"}
        layout = self.layout()

        for icon, name, meta, document_id in items:
            color = badge_colors.get(icon, "#F0C94C")
            item  = RecentItem(icon, name, meta, badge_color=color)
            # Insert before the final stretch
            item.clicked.connect(lambda doc_id=document_id: self.documentRequested.emit(doc_id))
            idx = layout.count() - 1
            layout.insertWidget(idx, item)
            self._items.append(item)
