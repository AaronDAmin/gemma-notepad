"""Recent documents dashboard — grid with search, filter chips and cards."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from app.core.models import Document, DocumentType
from app.storage.repositories import doc_repo
from app.ui.icons import load_svg_pixmap


class RecentDocCard(QWidget):
    """Large document card in the Recent Documents grid."""

    openRequested = Signal(object)

    def __init__(self, doc: Document, parent=None):
        super().__init__(parent)
        self.doc = doc
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(260, 180)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self._bg = "#F6ECCF"
        self._hover_bg = "#EEDBBA"

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        # Header: badge + type
        top = QHBoxLayout()
        badge = QFrame()
        badge.setFixedSize(36, 36)
        b_lay = QVBoxLayout(badge)
        b_lay.setContentsMargins(0, 0, 0, 0)
        b_lay.setAlignment(Qt.AlignCenter)
        b_lbl = QLabel()
        b_lbl.setAlignment(Qt.AlignCenter)

        if doc.doc_type == DocumentType.PDF:
            badge.setStyleSheet("background-color: #E04A4A; border-radius: 8px;")
            b_lbl.setText("PDF")
            b_lbl.setStyleSheet("color: #FFFFFF; font-size: 11px; font-weight: 700;")
            type_text = "PDF Textbook"
        elif doc.doc_type == DocumentType.IMAGE:
            badge.setStyleSheet("background-color: #3BA776; border-radius: 8px;")
            b_lbl.setPixmap(load_svg_pixmap("image_card_icon.svg", 20, color="#FFFFFF"))
            type_text = "Image Diagram"
        else:
            badge.setStyleSheet("background-color: #D4A017; border-radius: 8px;")
            b_lbl.setPixmap(load_svg_pixmap("text_card_icon.svg", 20, color="#FFFFFF"))
            type_text = "Study Notes"

        b_lay.addWidget(b_lbl)

        type_lbl = QLabel(type_text)
        type_lbl.setStyleSheet("color: #7A7465; font-size: 12px; font-weight: 500;")

        top.addWidget(badge)
        top.addWidget(type_lbl)
        top.addStretch(1)
        lay.addLayout(top)

        # Title
        title_lbl = QLabel(doc.name)
        title_lbl.setWordWrap(True)
        title_lbl.setStyleSheet("color: #1A1C1A; font-size: 15px; font-weight: 700;")
        lay.addWidget(title_lbl, 1)

        # Meta & Open button
        bottom = QHBoxLayout()
        meta = f"{doc.page_count} pages" if doc.page_count > 0 else "Editable note"
        meta_lbl = QLabel(meta)
        meta_lbl.setStyleSheet("color: #7A7465; font-size: 12px;")

        btn_open = QPushButton("Open")
        btn_open.setCursor(Qt.PointingHandCursor)
        btn_open.setStyleSheet(
            "QPushButton{background-color: #FFD04D; border-radius: 8px; color: #1A1C1A;"
            "font-size: 12.5px; font-weight: 700; padding: 5px 14px; border: none;}"
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
        self.setStyleSheet(f"QWidget{{background-color: {bg}; border-radius: 14px;}}")

    def enterEvent(self, e):
        self._apply_style(True)

    def leaveEvent(self, e):
        self._apply_style(False)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.openRequested.emit(self.doc)


class RecentDocumentsView(QWidget):
    """Recent documents view page."""

    documentOpened = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("recentView")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(
            "#recentView{background-color: #FFF8EC; border-radius: 18px;}"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(36, 32, 36, 32)
        root.setSpacing(20)

        # ── Header row ─────────────────────────────────────────────────────────
        top_bar = QHBoxLayout()
        title = QLabel("Recent Documents")
        title.setStyleSheet(
            "color: #1A1C1A; font-size: 24px; font-weight: 800; font-family: 'Segoe UI', sans-serif;"
        )
        top_bar.addWidget(title)
        top_bar.addStretch(1)

        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter recent documents…")
        self.search_input.setFixedWidth(240)
        self.search_input.setStyleSheet(
            "QLineEdit{background-color: #F6ECCF; border: 1px solid #E8DCB8; border-radius: 10px;"
            "color: #1A1C1A; font-size: 13px; padding: 6px 12px;}"
            "QLineEdit:focus{border-color: #FFD04D; background-color: #FFFFFF;}"
        )
        self.search_input.textChanged.connect(self._filter_docs)
        top_bar.addWidget(self.search_input)
        root.addLayout(top_bar)

        # ── Filter chips ───────────────────────────────────────────────────────
        chips_lay = QHBoxLayout()
        chips_lay.setSpacing(8)

        self._filter_type: str | None = None
        self._chip_btns: dict[str | None, QPushButton] = {}

        for key, label in [(None, "All Documents"), ("pdf", "PDFs"), ("image", "Images"), ("text", "Notes")]:
            btn = QPushButton(label)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, k=key: self._set_filter(k))
            self._chip_btns[key] = btn
            chips_lay.addWidget(btn)

        chips_lay.addStretch(1)
        root.addLayout(chips_lay)
        self._update_chip_styles()

        # ── Grid area ──────────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea{background: transparent; border: none;}")

        self._grid_container = QWidget()
        self._grid_container.setStyleSheet("background: transparent;")
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setSpacing(18)
        self._grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        scroll.setWidget(self._grid_container)
        root.addWidget(scroll, 1)

        self.refresh()

    def _set_filter(self, filter_type: str | None):
        self._filter_type = filter_type
        self._update_chip_styles()
        self._populate_grid()

    def _update_chip_styles(self):
        for key, btn in self._chip_btns.items():
            if key == self._filter_type:
                btn.setStyleSheet(
                    "QPushButton{background-color: #FFD04D; border-radius: 14px; color: #1A1C1A;"
                    "font-size: 12.5px; font-weight: 700; padding: 6px 16px; border: none;}"
                )
            else:
                btn.setStyleSheet(
                    "QPushButton{background-color: #F6ECCF; border-radius: 14px; color: #5A5445;"
                    "font-size: 12.5px; font-weight: 500; padding: 6px 16px; border: none;}"
                    "QPushButton:hover{background-color: #EEDBBA; color: #1A1C1A;}"
                )

    def _filter_docs(self, _):
        self._populate_grid()

    def refresh(self):
        self._populate_grid()

    def _populate_grid(self):
        # Clear existing
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        docs = doc_repo.get_recent(limit=30)
        query = self.search_input.text().strip().lower()

        filtered = []
        for d in docs:
            if self._filter_type and d.doc_type.value != self._filter_type:
                continue
            if query and query not in d.name.lower():
                continue
            filtered.append(d)

        if not filtered:
            empty = QLabel("No documents match your filter.")
            empty.setStyleSheet("color: #7A7465; font-size: 14px; font-style: italic;")
            self._grid_layout.addWidget(empty, 0, 0)
            return

        cols = 3
        for idx, d in enumerate(filtered):
            card = RecentDocCard(d)
            card.openRequested.connect(self.documentOpened)
            row = idx // cols
            col = idx % cols
            self._grid_layout.addWidget(card, row, col)
