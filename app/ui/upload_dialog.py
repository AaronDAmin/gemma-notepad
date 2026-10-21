"""Upload panel — floats on the right of the workspace."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QSizePolicy, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPixmap

from app.ui.icons import load_svg_pixmap


class UploadOptionCard(QWidget):
    """One upload type card (PDF / Image / Text)."""

    clicked = Signal()

    def __init__(self, icon_name: str, title: str, desc: str,
                 bg_color: str = "#F6ECCF", icon_bg: str = "#E8DBB8",
                 is_primary: bool = False, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._bg = bg_color
        self._icon_bg = icon_bg
        self._is_primary = is_primary

        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(76)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(12)

        # Left icon rounded square
        icon_box = QFrame()
        icon_box.setFixedSize(46, 46)
        icon_box.setStyleSheet(
            f"background-color: {icon_bg}; border-radius: 10px;"
        )
        icon_lay = QVBoxLayout(icon_box)
        icon_lay.setContentsMargins(0, 0, 0, 0)
        icon_lay.setAlignment(Qt.AlignCenter)

        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignCenter)
        pix = load_svg_pixmap(icon_name, 26)
        icon_lbl.setPixmap(pix)
        icon_lay.addWidget(icon_lbl)

        # Text column
        text_w = QWidget()
        text_w.setStyleSheet("background: transparent;")
        text_l = QVBoxLayout(text_w)
        text_l.setContentsMargins(0, 0, 0, 0)
        text_l.setSpacing(2)
        text_l.setAlignment(Qt.AlignVCenter)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(
            "color: #1A1C1A; font-size: 15px; font-weight: 700; background: transparent;"
        )
        desc_color = "#5A4E38" if is_primary else "#6B6554"
        lbl_desc = QLabel(desc)
        lbl_desc.setStyleSheet(
            f"color: {desc_color}; font-size: 11.5px; font-weight: 400; background: transparent;"
        )
        text_l.addWidget(lbl_title)
        text_l.addWidget(lbl_desc)

        # Chevron arrow
        arrow_color = "#1A1C1A" if is_primary else "#6B6554"
        arrow = QLabel("›")
        arrow.setStyleSheet(
            f"color: {arrow_color}; font-size: 20px; font-weight: 500; background: transparent;"
        )

        lay.addWidget(icon_box)
        lay.addWidget(text_w, 1)
        lay.addWidget(arrow)

        for child in self.findChildren(QWidget):
            child.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self._apply_style(False)

    def _apply_style(self, hovered: bool):
        bg = self._bg
        if hovered:
            if self._is_primary:
                bg = "#E8B228"
            else:
                bg = "#EEDBBA"
        self.setStyleSheet(
            f"QWidget{{background-color: {bg}; border-radius: 14px;}}"
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

    def __init__(self, doc_type: str, name: str, meta: str, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(54)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 4, 6, 4)
        lay.setSpacing(10)

        # Coloured badge
        badge = QFrame()
        badge.setFixedSize(34, 34)

        badge_lay = QVBoxLayout(badge)
        badge_lay.setContentsMargins(0, 0, 0, 0)
        badge_lay.setAlignment(Qt.AlignCenter)

        badge_lbl = QLabel()
        badge_lbl.setAlignment(Qt.AlignCenter)

        if doc_type.upper() == "PDF":
            badge.setStyleSheet("background-color: #E04A4A; border-radius: 6px;")
            badge_lbl.setText("PDF")
            badge_lbl.setStyleSheet("color: #FFFFFF; font-size: 10px; font-weight: 700; background: transparent;")
        elif doc_type.upper() == "IMAGE":
            badge.setStyleSheet("background-color: #3BA776; border-radius: 6px;")
            pix = load_svg_pixmap("image_card_icon.svg", 18, color="#FFFFFF")
            badge_lbl.setPixmap(pix)
        else:
            badge.setStyleSheet("background-color: #EAE0CB; border-radius: 6px;")
            pix = load_svg_pixmap("text_card_icon.svg", 18, color="#1A1C1A")
            badge_lbl.setPixmap(pix)

        badge_lay.addWidget(badge_lbl)

        # Text
        text_w = QWidget()
        text_w.setStyleSheet("background: transparent;")
        text_l = QVBoxLayout(text_w)
        text_l.setContentsMargins(0, 0, 0, 0)
        text_l.setSpacing(2)
        text_l.setAlignment(Qt.AlignVCenter)

        lbl_name = QLabel(name)
        lbl_name.setStyleSheet(
            "color: #1A1C1A; font-size: 13px; font-weight: 600; background: transparent;"
        )
        lbl_name.setMaximumWidth(220)
        lbl_name.setToolTip(name)

        lbl_meta = QLabel(meta)
        lbl_meta.setStyleSheet(
            "color: #8A9A8A; font-size: 11px; background: transparent;"
        )
        text_l.addWidget(lbl_name)
        text_l.addWidget(lbl_meta)

        menu_btn = QPushButton("⋮")
        menu_btn.setFixedSize(24, 24)
        menu_btn.setCursor(Qt.PointingHandCursor)
        menu_btn.setStyleSheet(
            "QPushButton{background: transparent; color: #8A9A8A; font-size: 16px; border: none; border-radius: 4px;}"
            "QPushButton:hover{background: #EADBBA; color: #1A1C1A;}"
        )

        lay.addWidget(badge)
        lay.addWidget(text_w, 1)
        lay.addWidget(menu_btn)

        for child in self.findChildren(QWidget):
            child.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit()

    def enterEvent(self, e):
        self.setStyleSheet("QWidget{background-color: rgba(0, 0, 0, 0.04); border-radius: 8px;}")

    def leaveEvent(self, e):
        self.setStyleSheet("")


class UploadPanel(QWidget):
    """
    Cream-coloured panel that slides in on the right.
    Width: 360px.
    """

    documentRequested = Signal(int)
    pdfRequested   = Signal()
    imageRequested = Signal()
    textRequested  = Signal()
    closeRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(360)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(-2, 0)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(shadow)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(0)

        # ── Header ─────────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        hdr.setSpacing(0)

        title_col = QVBoxLayout()
        title_col.setSpacing(4)

        lbl_title = QLabel("Upload Content")
        lbl_title.setStyleSheet(
            "color: #1A1C1A; font-size: 20px; font-weight: 700; background: transparent;"
        )

        lbl_sub = QLabel("Choose what you want to add to your\ndocument:")
        lbl_sub.setStyleSheet(
            "color: #4A4E4A; font-size: 12px; background: transparent; line-height: 1.3;"
        )

        title_col.addWidget(lbl_title)
        title_col.addWidget(lbl_sub)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(
            "QPushButton{background: transparent; border-radius: 6px; color: #8A9A8A; font-size: 14px; border: none;}"
            "QPushButton:hover{background: #EADBBA; color: #1A1C1A;}"
        )
        close_btn.clicked.connect(self.closeRequested)

        hdr.addLayout(title_col, 1)
        hdr.addWidget(close_btn, 0, Qt.AlignTop | Qt.AlignRight)
        root.addLayout(hdr)
        root.addSpacing(14)

        # ── Option cards ───────────────────────────────────────────────────────
        self.card_pdf = UploadOptionCard(
            "pdf_card_icon.svg", "PDF", "Import and view a PDF document",
            bg_color="#F4BC36", icon_bg="#E5A724", is_primary=True
        )
        self.card_img = UploadOptionCard(
            "image_card_icon.svg", "Image", "Add an image (PNG, JPG, etc.)",
            bg_color="#F6ECCF", icon_bg="#E8DBB8", is_primary=False
        )
        self.card_txt = UploadOptionCard(
            "text_card_icon.svg", "Text", "Create a new text document",
            bg_color="#F6ECCF", icon_bg="#E8DBB8", is_primary=False
        )

        self.card_pdf.clicked.connect(self.pdfRequested)
        self.card_img.clicked.connect(self.imageRequested)
        self.card_txt.clicked.connect(self.textRequested)

        root.addWidget(self.card_pdf)
        root.addSpacing(10)
        root.addWidget(self.card_img)
        root.addSpacing(10)
        root.addWidget(self.card_txt)
        root.addSpacing(22)

        # ── Recent uploads header ──────────────────────────────────────────────
        recent_hdr = QHBoxLayout()
        lbl_recent = QLabel("Recent Uploads")
        lbl_recent.setStyleSheet(
            "color: #1A1C1A; font-size: 16px; font-weight: 700; background: transparent;"
        )
        btn_see = QPushButton("See all")
        btn_see.setCursor(Qt.PointingHandCursor)
        btn_see.setStyleSheet(
            "QPushButton{background: transparent; color: #C58B24; font-size: 13px; font-weight: 600; border: none;}"
            "QPushButton:hover{color: #F0C94C;}"
        )
        recent_hdr.addWidget(lbl_recent)
        recent_hdr.addStretch()
        recent_hdr.addWidget(btn_see)
        root.addLayout(recent_hdr)
        root.addSpacing(8)

        # ── Recent items container ─────────────────────────────────────────────
        self._items: list[RecentItem] = []
        root.addStretch(1)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self.rect(), 18, 18)
        p.fillPath(path, QColor("#FCF1D8"))
        p.end()

    def refresh_recent(self, items: list[tuple[str, str, str, int]]):
        """
        Refresh recent items.
        items: list of (doc_type, name, meta, doc_id)
        """
        for item in self._items:
            self.layout().removeWidget(item)
            item.deleteLater()
        self._items.clear()

        layout = self.layout()
        for doc_type, name, meta, document_id in items:
            item = RecentItem(doc_type, name, meta)
            item.clicked.connect(lambda doc_id=document_id: self.documentRequested.emit(doc_id))
            idx = layout.count() - 1
            layout.insertWidget(idx, item)
            self._items.append(item)
