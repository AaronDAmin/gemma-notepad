"""Home / Empty Workspace view — welcome screen and quick actions."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QCursor

from app.core.models import Document, DocumentType
from app.storage.repositories import doc_repo
from app.ui.icons import load_svg_pixmap


class ActionCard(QWidget):
    """One quick-action card on the welcome screen."""

    clicked = Signal()

    def __init__(self, icon_name: str, title: str, desc: str,
                 icon_bg: str = "#E8DCB8", parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(120)

        self._bg = "#F6ECCF"
        self._hover_bg = "#EEDBBA"
        self._icon_bg = icon_bg

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(10)
        lay.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(12)

        icon_box = QFrame()
        icon_box.setFixedSize(40, 40)
        icon_box.setStyleSheet(
            f"background-color: {icon_bg}; border-radius: 10px;"
        )
        ib_lay = QVBoxLayout(icon_box)
        ib_lay.setContentsMargins(0, 0, 0, 0)
        ib_lay.setAlignment(Qt.AlignCenter)

        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignCenter)
        pix = load_svg_pixmap(icon_name, 22, color="#1A1C1A")
        icon_lbl.setPixmap(pix)
        ib_lay.addWidget(icon_lbl)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(
            "color: #1A1C1A; font-size: 15px; font-weight: 700; background: transparent;"
        )

        top_row.addWidget(icon_box)
        top_row.addWidget(lbl_title, 1)
        lay.addLayout(top_row)

        lbl_desc = QLabel(desc)
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet(
            "color: #5A5445; font-size: 12px; font-weight: 400; background: transparent;"
        )
        lay.addWidget(lbl_desc)

        for child in self.findChildren(QWidget):
            child.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self._apply_style(False)

    def _apply_style(self, hovered: bool):
        bg = self._hover_bg if hovered else self._bg
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


class RecentCard(QWidget):
    """Card representing a recently opened document."""

    clicked = Signal()

    def __init__(self, doc: Document, parent=None):
        super().__init__(parent)
        self.doc = doc
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(82)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(12)

        # Badge
        badge = QFrame()
        badge.setFixedSize(38, 38)
        b_lay = QVBoxLayout(badge)
        b_lay.setContentsMargins(0, 0, 0, 0)
        b_lay.setAlignment(Qt.AlignCenter)
        b_lbl = QLabel()
        b_lbl.setAlignment(Qt.AlignCenter)

        if doc.doc_type == DocumentType.PDF:
            badge.setStyleSheet("background-color: #E04A4A; border-radius: 8px;")
            b_lbl.setText("PDF")
            b_lbl.setStyleSheet("color: #FFFFFF; font-size: 11px; font-weight: 700; background: transparent;")
        elif doc.doc_type == DocumentType.IMAGE:
            badge.setStyleSheet("background-color: #3BA776; border-radius: 8px;")
            pix = load_svg_pixmap("image_card_icon.svg", 20, color="#FFFFFF")
            b_lbl.setPixmap(pix)
        else:
            badge.setStyleSheet("background-color: #EAE0CB; border-radius: 8px;")
            pix = load_svg_pixmap("text_card_icon.svg", 20, color="#1A1C1A")
            b_lbl.setPixmap(pix)

        b_lay.addWidget(b_lbl)

        # Info
        info_w = QWidget()
        info_w.setStyleSheet("background: transparent;")
        info_l = QVBoxLayout(info_w)
        info_l.setContentsMargins(0, 0, 0, 0)
        info_l.setSpacing(2)

        title = QLabel(doc.name)
        title.setStyleSheet("color: #1A1C1A; font-size: 13.5px; font-weight: 600; background: transparent;")
        meta = f"{doc.page_count} pages" if doc.page_count > 0 else "Note"
        sub = QLabel(f"Page {doc.current_page} • {meta}")
        sub.setStyleSheet("color: #7A7465; font-size: 11.5px; background: transparent;")

        info_l.addWidget(title)
        info_l.addWidget(sub)

        # Arrow
        arrow = QLabel("›")
        arrow.setStyleSheet("color: #9A9485; font-size: 20px; font-weight: bold; background: transparent;")

        lay.addWidget(badge)
        lay.addWidget(info_w, 1)
        lay.addWidget(arrow)

        for child in self.findChildren(QWidget):
            child.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self._apply_style(False)

    def _apply_style(self, hovered: bool):
        bg = "#EEDBBA" if hovered else "#F6ECCF"
        self.setStyleSheet(f"QWidget{{background-color: {bg}; border-radius: 12px;}}")

    def enterEvent(self, e):
        self._apply_style(True)

    def leaveEvent(self, e):
        self._apply_style(False)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit()


class HomeView(QWidget):
    """
    Home / Empty workspace welcome screen.
    Displays quick action cards and recent documents.
    """

    openPdfRequested       = Signal()
    importImageRequested   = Signal()
    newNoteRequested       = Signal()
    generateQuizRequested  = Signal()
    documentOpened         = Signal(object)
    viewAllRecentRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("homeView")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(
            "#homeView{background-color: #FFF8EC; border-radius: 18px;}"
        )

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea{background: transparent; border: none;}")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        root = QVBoxLayout(content)
        root.setContentsMargins(40, 36, 40, 36)
        root.setSpacing(24)
        root.setAlignment(Qt.AlignTop)

        # ── Greeting Header ────────────────────────────────────────────────────
        header = QVBoxLayout()
        header.setSpacing(6)

        title = QLabel("Welcome to GemmaNotepad1")
        title.setStyleSheet(
            "color: #1A1C1A; font-size: 26px; font-weight: 800; font-family: 'Segoe UI', sans-serif;"
        )
        subtitle = QLabel(
            "Your AI-powered study companion. Open a textbook, inspect schemas, "
            "take notes, or generate quizzes to master your courses."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(
            "color: #6A6556; font-size: 14px; font-weight: 400; font-family: 'Segoe UI', sans-serif;"
        )

        header.addWidget(title)
        header.addWidget(subtitle)
        root.addLayout(header)

        # ── Action Cards Grid ──────────────────────────────────────────────────
        grid = QGridLayout()
        grid.setSpacing(16)

        self.card_pdf = ActionCard(
            "pdf_card_icon.svg", "Open PDF",
            "Browse and study PDF textbooks with AI explanations",
            icon_bg="#F3C3B8"
        )
        self.card_img = ActionCard(
            "image_card_icon.svg", "Import Image",
            "View and analyze ER diagrams, schemas, and photos",
            icon_bg="#BDE3D0"
        )
        self.card_note = ActionCard(
            "text_card_icon.svg", "New Note",
            "Write and format study summaries and notes",
            icon_bg="#EADFBE"
        )
        self.card_quiz = ActionCard(
            "quiz_badge.svg", "Generate Quiz",
            "Create interactive multiple-choice quizzes with AI",
            icon_bg="#FDE598"
        )

        self.card_pdf.clicked.connect(self.openPdfRequested)
        self.card_img.clicked.connect(self.importImageRequested)
        self.card_note.clicked.connect(self.newNoteRequested)
        self.card_quiz.clicked.connect(self.generateQuizRequested)

        grid.addWidget(self.card_pdf,  0, 0)
        grid.addWidget(self.card_img,  0, 1)
        grid.addWidget(self.card_note, 1, 0)
        grid.addWidget(self.card_quiz, 1, 1)
        root.addLayout(grid)

        # ── Recent Documents Section ───────────────────────────────────────────
        rec_header = QHBoxLayout()
        rec_title = QLabel("Recent Documents")
        rec_title.setStyleSheet(
            "color: #1A1C1A; font-size: 18px; font-weight: 700;"
        )
        self.btn_view_all = QPushButton("View All ›")
        self.btn_view_all.setCursor(Qt.PointingHandCursor)
        self.btn_view_all.setStyleSheet(
            "QPushButton{color: #D4A017; font-size: 13px; font-weight: 600; border: none; background: transparent;}"
            "QPushButton:hover{color: #B5840E;}"
        )
        self.btn_view_all.clicked.connect(self.viewAllRecentRequested)

        rec_header.addWidget(rec_title)
        rec_header.addStretch(1)
        rec_header.addWidget(self.btn_view_all)
        root.addLayout(rec_header)

        self._recent_container = QVBoxLayout()
        self._recent_container.setSpacing(10)
        root.addLayout(self._recent_container)

        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        self.refresh_recent()

    def refresh_recent(self):
        # Clear existing
        while self._recent_container.count():
            item = self._recent_container.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        recent = doc_repo.get_recent(limit=4)
        if not recent:
            empty = QLabel("No recent documents yet. Open a PDF or create a note to begin.")
            empty.setStyleSheet("color: #8A8475; font-size: 13px; font-style: italic;")
            self._recent_container.addWidget(empty)
            return

        for doc in recent:
            c = RecentCard(doc)
            c.clicked.connect(lambda d=doc: self.documentOpened.emit(d))
            self._recent_container.addWidget(c)
