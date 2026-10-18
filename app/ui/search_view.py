"""Document search interface — full-text search across documents and notes."""
from __future__ import annotations
import os
import pymupdf as fitz
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal

from app.core.models import Document, DocumentType
from app.storage.repositories import doc_repo


class SearchResultItem(QWidget):
    openRequested = Signal(object, int)

    def __init__(self, doc: Document, page: int, snippet: str, query: str, parent=None):
        super().__init__(parent)
        self.doc = doc
        self.page = page
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(94)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(6)

        top = QHBoxLayout()
        title = QLabel(f"{doc.name} • Page {page}")
        title.setStyleSheet("color: #1A1C1A; font-size: 14px; font-weight: 700;")

        btn_open = QPushButton("Open Page ›")
        btn_open.setCursor(Qt.PointingHandCursor)
        btn_open.setStyleSheet(
            "QPushButton{background-color: #FFD04D; border-radius: 6px; color: #1A1C1A;"
            "font-size: 12px; font-weight: 700; padding: 4px 12px; border: none;}"
            "QPushButton:hover{background-color: #E8B93A;}"
        )
        btn_open.clicked.connect(lambda: self.openRequested.emit(self.doc, self.page))

        top.addWidget(title)
        top.addStretch(1)
        top.addWidget(btn_open)
        lay.addLayout(top)

        # Snippet with highlight
        snippet_lbl = QLabel(snippet)
        snippet_lbl.setWordWrap(True)
        snippet_lbl.setStyleSheet("color: #5A5445; font-size: 12.5px; line-height: 1.4;")
        lay.addWidget(snippet_lbl)

        self.setStyleSheet("QWidget{background-color: #F6ECCF; border-radius: 12px;}")

    def enterEvent(self, e):
        self.setStyleSheet("QWidget{background-color: #EEDBBA; border-radius: 12px;}")

    def leaveEvent(self, e):
        self.setStyleSheet("QWidget{background-color: #F6ECCF; border-radius: 12px;}")

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.openRequested.emit(self.doc, self.page)


class SearchView(QWidget):
    """Search interface for finding text snippets in documents and notes."""

    openDocumentAtPage = Signal(object, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("searchView")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(
            "#searchView{background-color: #FFF8EC; border-radius: 18px;}"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(36, 32, 36, 32)
        root.setSpacing(20)

        # ── Header ─────────────────────────────────────────────────────────────
        title = QLabel("Search in Documents")
        title.setStyleSheet(
            "color: #1A1C1A; font-size: 24px; font-weight: 800; font-family: 'Segoe UI', sans-serif;"
        )
        root.addWidget(title)

        # ── Search Bar Row ─────────────────────────────────────────────────────
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search terms, concepts, definitions… (e.g. 'DBMS', 'Normalization')")
        self.search_input.setFixedHeight(44)
        self.search_input.setStyleSheet(
            "QLineEdit{background-color: #F6ECCF; border: 1px solid #E8DCB8; border-radius: 12px;"
            "color: #1A1C1A; font-size: 14px; padding: 0 16px;}"
            "QLineEdit:focus{border-color: #FFD04D; background-color: #FFFFFF;}"
        )
        self.search_input.returnPressed.connect(self._do_search)

        btn_search = QPushButton("Search")
        btn_search.setFixedHeight(44)
        btn_search.setCursor(Qt.PointingHandCursor)
        btn_search.setStyleSheet(
            "QPushButton{background-color: #FFD04D; border-radius: 12px; color: #1A1C1A;"
            "font-size: 14px; font-weight: 700; padding: 0 24px; border: none;}"
            "QPushButton:hover{background-color: #E8B93A;}"
        )
        btn_search.clicked.connect(self._do_search)

        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(btn_search)
        root.addLayout(search_row)

        # ── Results Area ───────────────────────────────────────────────────────
        self.status_lbl = QLabel("Enter a keyword and press Search to find passages.")
        self.status_lbl.setStyleSheet("color: #7A7465; font-size: 13px; font-style: italic;")
        root.addWidget(self.status_lbl)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea{background: transparent; border: none;}")

        self._results_w = QWidget()
        self._results_w.setStyleSheet("background: transparent;")
        self._results_lay = QVBoxLayout(self._results_w)
        self._results_lay.setSpacing(10)
        self._results_lay.setAlignment(Qt.AlignTop)

        scroll.setWidget(self._results_w)
        root.addWidget(scroll, 1)

    def _do_search(self):
        query = self.search_input.text().strip()
        if not query:
            return

        while self._results_lay.count():
            item = self._results_lay.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        docs = doc_repo.get_recent(limit=30)
        results = []

        q_lower = query.lower()

        for d in docs:
            if d.doc_type == DocumentType.PDF and d.file_path and os.path.exists(d.file_path):
                try:
                    pdf = fitz.open(d.file_path)
                    for page_num in range(len(pdf)):
                        text = pdf[page_num].get_text()
                        if q_lower in text.lower():
                            idx = text.lower().find(q_lower)
                            start = max(0, idx - 60)
                            end = min(len(text), idx + len(query) + 80)
                            snippet = "…" + text[start:end].replace("\n", " ").strip() + "…"
                            results.append((d, page_num + 1, snippet))
                            if len(results) >= 20:
                                break
                    pdf.close()
                except Exception:
                    pass
            elif d.doc_type == DocumentType.TEXT and d.content:
                if q_lower in d.content.lower():
                    idx = d.content.lower().find(q_lower)
                    start = max(0, idx - 60)
                    end = min(len(d.content), idx + len(query) + 80)
                    snippet = "…" + d.content[start:end].replace("\n", " ").strip() + "…"
                    results.append((d, 1, snippet))

        self.status_lbl.setText(f"Found {len(results)} matches for '{query}':")
        for d, page, snip in results:
            item = SearchResultItem(d, page, snip, query)
            item.openRequested.connect(self.openDocumentAtPage)
            self._results_lay.addWidget(item)

        if not results:
            empty = QLabel(f"No results found for '{query}'. Try searching for 'DBMS' or 'Data'.")
            empty.setStyleSheet("color: #7A7465; font-size: 13.5px; font-style: italic;")
            self._results_lay.addWidget(empty)
