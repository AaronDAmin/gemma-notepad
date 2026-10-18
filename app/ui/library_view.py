"""Library view — organized document collection with categories and upload action."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QSizePolicy, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal

from app.core.models import Document, DocumentType
from app.storage.repositories import doc_repo
from app.ui.icons import load_svg_pixmap


class LibraryCard(QWidget):
    openRequested = Signal(object)
    deleteRequested = Signal(object)

    def __init__(self, doc: Document, parent=None):
        super().__init__(parent)
        self.doc = doc
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(240, 160)

        self._bg = "#F6ECCF"
        self._hover_bg = "#EEDBBA"

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(8)

        top = QHBoxLayout()
        badge = QFrame()
        badge.setFixedSize(32, 32)
        b_lay = QVBoxLayout(badge)
        b_lay.setContentsMargins(0, 0, 0, 0)
        b_lay.setAlignment(Qt.AlignCenter)
        b_lbl = QLabel()
        b_lbl.setAlignment(Qt.AlignCenter)

        if doc.doc_type == DocumentType.PDF:
            badge.setStyleSheet("background-color: #E04A4A; border-radius: 6px;")
            b_lbl.setText("PDF")
            b_lbl.setStyleSheet("color: #FFFFFF; font-size: 10px; font-weight: 700;")
        elif doc.doc_type == DocumentType.IMAGE:
            badge.setStyleSheet("background-color: #3BA776; border-radius: 6px;")
            b_lbl.setPixmap(load_svg_pixmap("image_card_icon.svg", 18, color="#FFFFFF"))
        else:
            badge.setStyleSheet("background-color: #D4A017; border-radius: 6px;")
            b_lbl.setPixmap(load_svg_pixmap("text_card_icon.svg", 18, color="#FFFFFF"))

        b_lay.addWidget(b_lbl)

        btn_more = QPushButton("⋮")
        btn_more.setFixedSize(22, 22)
        btn_more.setStyleSheet(
            "QPushButton{color: #7A7465; font-size: 16px; border: none; background: transparent;}"
            "QPushButton:hover{color: #1A1C1A; background-color: #E2CF9F; border-radius: 4px;}"
        )

        top.addWidget(badge)
        top.addStretch(1)
        top.addWidget(btn_more)
        lay.addLayout(top)

        title = QLabel(doc.name)
        title.setWordWrap(True)
        title.setStyleSheet("color: #1A1C1A; font-size: 14px; font-weight: 700;")
        lay.addWidget(title, 1)

        bottom = QHBoxLayout()
        meta = f"{doc.page_count} pages" if doc.page_count > 0 else "Note"
        meta_lbl = QLabel(meta)
        meta_lbl.setStyleSheet("color: #7A7465; font-size: 11.5px;")

        btn_open = QPushButton("Open")
        btn_open.setCursor(Qt.PointingHandCursor)
        btn_open.setStyleSheet(
            "QPushButton{background-color: #FFD04D; border-radius: 6px; color: #1A1C1A;"
            "font-size: 12px; font-weight: 700; padding: 4px 12px; border: none;}"
            "QPushButton:hover{background-color: #E8B93A;}"
        )
        btn_open.clicked.connect(lambda: self.openRequested.emit(self.doc))

        bottom.addWidget(meta_lbl)
        bottom.addStretch(1)
        bottom.addWidget(btn_open)
        lay.addLayout(bottom)

        self._apply_style(False)

    def _apply_style(self, hovered: bool):
        bg = self._hover_bg if hovered else self._bg
        self.setStyleSheet(f"QWidget{{background-color: {bg}; border-radius: 12px;}}")

    def enterEvent(self, e):
        self._apply_style(True)

    def leaveEvent(self, e):
        self._apply_style(False)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.openRequested.emit(self.doc)


class LibraryView(QWidget):
    """Document library view with category tree and cards grid."""

    documentOpened  = Signal(object)
    uploadRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("libraryView")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(
            "#libraryView{background-color: #FFF8EC; border-radius: 18px;}"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(36, 32, 36, 32)
        root.setSpacing(20)

        # ── Top bar ────────────────────────────────────────────────────────────
        top_bar = QHBoxLayout()
        title = QLabel("Document Library")
        title.setStyleSheet(
            "color: #1A1C1A; font-size: 24px; font-weight: 800; font-family: 'Segoe UI', sans-serif;"
        )
        top_bar.addWidget(title)
        top_bar.addStretch(1)

        btn_upload = QPushButton("＋  Upload Document")
        btn_upload.setCursor(Qt.PointingHandCursor)
        btn_upload.setStyleSheet(
            "QPushButton{background-color: #FFD04D; border-radius: 10px; color: #1A1C1A;"
            "font-size: 13px; font-weight: 700; padding: 8px 18px; border: none;}"
            "QPushButton:hover{background-color: #E8B93A;}"
        )
        btn_upload.clicked.connect(self.uploadRequested)
        top_bar.addWidget(btn_upload)
        root.addLayout(top_bar)

        # ── Body: Categories sidebar + Document Grid ───────────────────────────
        body = QHBoxLayout()
        body.setSpacing(24)

        # Categories list
        cat_box = QWidget()
        cat_box.setFixedWidth(200)
        cat_box.setStyleSheet(
            "background-color: #F6ECCF; border-radius: 14px;"
        )
        cat_lay = QVBoxLayout(cat_box)
        cat_lay.setContentsMargins(12, 14, 12, 14)
        cat_lay.setSpacing(6)

        cat_title = QLabel("CATEGORIES")
        cat_title.setStyleSheet("color: #7A7465; font-size: 11px; font-weight: 700; padding-left: 6px;")
        cat_lay.addWidget(cat_title)

        self._active_cat = "All Documents"
        self._cat_buttons = []
        for cat in ["All Documents", "Database Systems", "Operating Systems", "Study Notes", "Favorites"]:
            btn = QPushButton(cat)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, c=cat: self._select_category(c))
            self._cat_buttons.append(btn)
            cat_lay.addWidget(btn)

        cat_lay.addStretch(1)
        body.addWidget(cat_box)
        self._update_cat_styles()

        # Grid area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea{background: transparent; border: none;}")

        self._grid_container = QWidget()
        self._grid_container.setStyleSheet("background: transparent;")
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setSpacing(16)
        self._grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        scroll.setWidget(self._grid_container)
        body.addWidget(scroll, 1)

        root.addLayout(body, 1)
        self.refresh()

    def _select_category(self, cat: str):
        self._active_cat = cat
        self._update_cat_styles()
        self.refresh()

    def _update_cat_styles(self):
        for btn in self._cat_buttons:
            if btn.text() == self._active_cat:
                btn.setStyleSheet(
                    "QPushButton{background-color: #FFD04D; border-radius: 8px; color: #1A1C1A;"
                    "font-size: 13px; font-weight: 700; text-align: left; padding: 8px 12px; border: none;}"
                )
            else:
                btn.setStyleSheet(
                    "QPushButton{background-color: transparent; border-radius: 8px; color: #4A4538;"
                    "font-size: 13px; font-weight: 500; text-align: left; padding: 8px 12px; border: none;}"
                    "QPushButton:hover{background-color: #EEDBBA; color: #1A1C1A;}"
                )

    def refresh(self):
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        docs = doc_repo.get_recent(limit=30)
        cols = 3
        for idx, doc in enumerate(docs):
            card = LibraryCard(doc)
            card.openRequested.connect(self.documentOpened)
            row = idx // cols
            col = idx % cols
            self._grid_layout.addWidget(card, row, col)
