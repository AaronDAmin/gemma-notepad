"""PDF viewer — real rendering via PyMuPDF with mouse text selection."""
from __future__ import annotations
import pymupdf as fitz
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QComboBox, QScrollArea, QFrame, QSizePolicy,
    QMessageBox, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QRect, QPoint, QRectF
from PySide6.QtGui import QPainter, QColor, QPixmap, QPen, QCursor, QPainterPath

from app.services.pdf_service import pdf_service
from app.ui.icons import load_svg_pixmap


class PDFToolbar(QWidget):
    zoomChanged   = Signal(int)
    prevRequested = Signal()
    nextRequested = Signal()
    searchClicked = Signal()
    bookClicked   = Signal()
    bookmarkClicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(48)
        self.setStyleSheet("QWidget{background-color: transparent; border: none;}")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 0, 18, 0)
        lay.setSpacing(6)
        lay.setAlignment(Qt.AlignVCenter)

        # ── Left: Document icon ────────────────────────────────────────────────
        self.doc_icon_lbl = QLabel()
        self.doc_icon_lbl.setFixedSize(26, 26)
        self.doc_icon_lbl.setAlignment(Qt.AlignCenter)
        pix_doc = load_svg_pixmap("doc_icon.svg", 18)
        self.doc_icon_lbl.setPixmap(pix_doc)
        lay.addWidget(self.doc_icon_lbl)
        lay.addSpacing(4)

        # ── Navigation arrows ──────────────────────────────────────────────────
        def nav_btn(text: str, tip: str) -> QPushButton:
            b = QPushButton(text)
            b.setFixedSize(26, 26)
            b.setCursor(Qt.PointingHandCursor)
            b.setToolTip(tip)
            b.setStyleSheet(
                "QPushButton{"
                "background: transparent; color: #4A4E4A; font-size: 16px; font-weight: 600;"
                "border: none; border-radius: 6px;"
                "}"
                "QPushButton:hover{background-color: #EEDBBA; color: #1A1C1A;}"
                "QPushButton:pressed{background-color: #DDC8A0;}"
            )
            return b

        self.btn_prev = nav_btn("‹", "Previous page")
        self.btn_next = nav_btn("›", "Next page")
        lay.addWidget(self.btn_prev)
        lay.addWidget(self.btn_next)
        lay.addSpacing(6)

        # ── Page indicator box ─────────────────────────────────────────────────
        page_box = QWidget()
        page_box.setFixedHeight(26)
        page_box.setStyleSheet(
            "QWidget{"
            "background-color: #F6ECCF; border: 1px solid #E8DCB8; border-radius: 6px;"
            "}"
        )
        pb_lay = QHBoxLayout(page_box)
        pb_lay.setContentsMargins(6, 0, 8, 0)
        pb_lay.setSpacing(4)

        self.page_input = QLineEdit("1")
        self.page_input.setFixedWidth(22)
        self.page_input.setAlignment(Qt.AlignCenter)
        self.page_input.setStyleSheet(
            "QLineEdit{background: transparent; border: none; color: #1A1C1A; font-size: 12.5px; font-weight: 600;}"
        )

        self.page_total = QLabel("/ 20")
        self.page_total.setStyleSheet(
            "color: #8A9A8A; font-size: 12.5px; font-weight: 500; background: transparent;"
        )

        pb_lay.addWidget(self.page_input)
        pb_lay.addWidget(self.page_total)
        lay.addWidget(page_box)
        lay.addSpacing(6)

        # ── Zoom combo ─────────────────────────────────────────────────────────
        self.zoom_combo = QComboBox()
        self.zoom_combo.setFixedSize(84, 26)
        self.zoom_combo.setStyleSheet(
            "QComboBox{"
            "background-color: #F6ECCF; border: 1px solid #E8DCB8; border-radius: 6px;"
            "color: #1A1C1A; font-size: 12px; font-weight: 500; padding-left: 8px;"
            "}"
            "QComboBox::drop-down{border: none; width: 18px;}"
            "QComboBox::down-arrow{"
            "image: none; border-left: 4px solid transparent; border-right: 4px solid transparent;"
            "border-top: 5px solid #4A4E4A; margin-right: 6px;"
            "}"
            "QComboBox QAbstractItemView{"
            "background-color: #FCF6EC; border: 1px solid #E8DCB8; border-radius: 6px;"
            "color: #1A1C1A; selection-background-color: #FFD04D; selection-color: #1A1C1A;"
            "}"
        )
        for lvl in [50, 75, 100, 125, 150, 175, 200]:
            self.zoom_combo.addItem(f"{lvl}%", lvl)
        self.zoom_combo.setCurrentText("125%")
        lay.addWidget(self.zoom_combo)

        lay.addStretch(1)

        # ── Right toolbar tools ────────────────────────────────────────────────
        def tool_btn(icon_name: str, tip: str, click_signal) -> QPushButton:
            b = QPushButton()
            b.setFixedSize(28, 28)
            b.setCursor(Qt.PointingHandCursor)
            b.setToolTip(tip)
            pix = load_svg_pixmap(icon_name, 17)
            b.setIcon(pix)
            b.setIconSize(pix.size())
            b.setStyleSheet(
                "QPushButton{background: transparent; border: none; border-radius: 6px;}"
                "QPushButton:hover{background-color: #EEDBBA;}"
            )
            b.clicked.connect(click_signal)
            return b

        self.btn_search   = tool_btn("search_magnifier.svg", "Search in document", self.searchClicked)
        self.btn_book     = tool_btn("book_view.svg", "Toggle book view", self.bookClicked)
        self.btn_bookmark = tool_btn("bookmark_ribbon.svg", "Add bookmark", self.bookmarkClicked)

        lay.addWidget(self.btn_search)
        lay.addWidget(self.btn_book)
        lay.addWidget(self.btn_bookmark)

        self.btn_prev.clicked.connect(self.prevRequested)
        self.btn_next.clicked.connect(self.nextRequested)
        self.zoom_combo.currentIndexChanged.connect(
            lambda _: self.zoomChanged.emit(self.zoom_combo.currentData())
        )
        self.page_input.returnPressed.connect(self._on_page_entered)

    def update_display(self, current: int, total: int):
        self.page_input.setText(str(current))
        self.page_total.setText(f"/ {total}")

    def current_zoom(self) -> int:
        return self.zoom_combo.currentData() or 125

    def _on_page_entered(self):
        try:
            page = int(self.page_input.text())
            viewer = self.parent()
            if viewer and hasattr(viewer, "go_to_page"):
                viewer.go_to_page(page - 1)
        except ValueError:
            pass


class PDFPageWidget(QWidget):
    """
    Renders PDF page with rounded corners, drop shadow, and selection overlays.
    """

    textSelected = Signal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.IBeamCursor)
        self.setAttribute(Qt.WA_Hover, True)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 45))
        self.setGraphicsEffect(shadow)

        self._page_num: int = 0
        self._zoom: float = 1.0
        self._blocks: list[dict] = []
        self._sel_start: QPoint | None = None
        self._sel_rect: QRect | None = None
        self._sel_text: str = ""
        self._highlight_rects: list[QRect] = []
        self._pixmap: QPixmap | None = None

    def set_page(self, pixmap: QPixmap, blocks: list[dict],
                 page_num: int, zoom: float):
        self._pixmap = pixmap
        self._blocks = blocks
        self._page_num = page_num
        self._zoom = zoom
        self._sel_rect = None
        self._sel_text = ""
        self.setFixedSize(pixmap.size())
        self.update()

    def set_highlight_rects(self, rects: list[QRect]):
        self._highlight_rects = rects
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._sel_start = event.pos()
            self._sel_rect  = None
            self._sel_text  = ""
            self._highlight_rects = []
            self.update()

    def mouseMoveEvent(self, event):
        if self._sel_start and event.buttons() & Qt.LeftButton:
            x0 = min(self._sel_start.x(), event.pos().x())
            y0 = min(self._sel_start.y(), event.pos().y())
            x1 = max(self._sel_start.x(), event.pos().x())
            y1 = max(self._sel_start.y(), event.pos().y())
            self._sel_rect = QRect(x0, y0, x1 - x0, y1 - y0)
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._sel_rect:
            self._sel_text = self._extract_selected_text()
            if self._sel_text.strip():
                self.textSelected.emit(self._sel_text.strip(), self._page_num)
            self.update()
        self._sel_start = None

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        # Clip to rounded rectangle
        clip_path = QPainterPath()
        clip_path.addRoundedRect(QRectF(self.rect()), 10, 10)
        p.setClipPath(clip_path)

        if self._pixmap and not self._pixmap.isNull():
            p.drawPixmap(self.rect(), self._pixmap)

        # Draw persistent highlighted rects (warm yellow)
        for hr in self._highlight_rects:
            hpath = QPainterPath()
            hpath.addRoundedRect(QRectF(hr), 3, 3)
            p.fillPath(hpath, QColor(251, 214, 101, 190))

        # Draw active selection rect
        if self._sel_rect and not self._sel_rect.isEmpty():
            hpath = QPainterPath()
            hpath.addRoundedRect(QRectF(self._sel_rect), 3, 3)
            p.fillPath(hpath, QColor(251, 214, 101, 150))
            p.setPen(QPen(QColor(212, 160, 23, 180), 1))
            p.drawPath(hpath)

        p.end()

    def _extract_selected_text(self) -> str:
        if not self._sel_rect or not self._blocks:
            return ""
        z = self._zoom
        sel_x0 = self._sel_rect.left()   / z
        sel_y0 = self._sel_rect.top()    / z
        sel_x1 = self._sel_rect.right()  / z
        sel_y1 = self._sel_rect.bottom() / z
        sel_fitz = fitz.Rect(sel_x0, sel_y0, sel_x1, sel_y1)

        texts = []
        for block in self._blocks:
            if block["rect"].intersects(sel_fitz):
                texts.append(block["text"].replace("\n", " ").strip())
        return " ".join(texts)


class PDFViewer(QWidget):
    textSelected = Signal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("workspacePanel")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(
            "QWidget#workspacePanel{"
            "background-color: #FAF0DA;"
            "border-radius: 18px;"
            "}"
        )

        self._doc: fitz.Document | None = None
        self._current_page: int = 0
        self._total_pages: int = 0
        self._zoom: float = 1.0
        self._doc_name: str = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 8)
        root.setSpacing(2)

        self.toolbar = PDFToolbar(self)
        root.addWidget(self.toolbar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.scroll.setStyleSheet(
            "QScrollArea{background: transparent; border: none;}"
            "QScrollArea > QWidget{background: transparent;}"
        )

        # Container widget inside scroll area to center and pad the page sheet
        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        c_lay = QVBoxLayout(self._container)
        c_lay.setContentsMargins(16, 8, 16, 16)
        c_lay.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        self.page_widget = PDFPageWidget()
        self.page_widget.textSelected.connect(
            lambda t, p: self.textSelected.emit(t, p + 1)
        )
        self.page_widget.setMouseTracking(True)
        c_lay.addWidget(self.page_widget, 0, Qt.AlignHCenter)

        self.scroll.setWidget(self._container)
        root.addWidget(self.scroll, 1)

        self.toolbar.prevRequested.connect(self._prev)
        self.toolbar.nextRequested.connect(self._next)
        self.toolbar.zoomChanged.connect(self._on_zoom)

    def load_pdf(self, path: str, doc_name: str = "", highlight_text: str | None = None):
        try:
            if self._doc:
                self._doc.close()
            self._doc          = pdf_service.open(path)
            self._total_pages  = self._doc.page_count
            self._current_page = 0
            self._doc_name     = doc_name or path.split("/")[-1].split("\\")[-1]
            self._render(highlight_text)
        except Exception as e:
            QMessageBox.critical(self, "Error opening PDF", str(e))

    def go_to_page(self, page_index: int):
        if 0 <= page_index < self._total_pages:
            self._current_page = page_index
            self._render()

    def current_page_1based(self) -> int:
        return self._current_page + 1

    def get_context_for_selection(self, selected_text: str) -> str:
        if self._doc is None:
            return ""
        return pdf_service.get_context_around(
            self._doc, self._current_page, selected_text
        )

    def highlight_phrase(self, phrase: str) -> QRect | None:
        if not self._doc:
            return None
        page = self._doc[self._current_page]
        rects = page.search_for(phrase)
        if not rects:
            return None

        qrects = []
        for r in rects:
            qr = QRect(
                int(r.x0 * self._zoom),
                int(r.y0 * self._zoom),
                int((r.x1 - r.x0) * self._zoom),
                int((r.y1 - r.y0) * self._zoom)
            )
            qrects.append(qr)

        self.page_widget.set_highlight_rects(qrects)
        return qrects[0] if qrects else None

    def _render(self, highlight_text: str | None = None):
        if self._doc is None:
            return
        pixmap = pdf_service.render_page(self._doc, self._current_page, self._zoom)
        blocks = pdf_service.get_text_blocks(self._doc, self._current_page)
        self.page_widget.set_page(pixmap, blocks, self._current_page, self._zoom)
        self.toolbar.update_display(self._current_page + 1, self._total_pages)

        if highlight_text:
            self.highlight_phrase(highlight_text)

        self.scroll.verticalScrollBar().setValue(0)

    def _prev(self):
        if self._current_page > 0:
            self._current_page -= 1
            self._render()

    def _next(self):
        if self._current_page < self._total_pages - 1:
            self._current_page += 1
            self._render()

    def _on_zoom(self, level_pct: int):
        self._zoom = level_pct / 100.0
        self._render()

    def closeEvent(self, event):
        if self._doc:
            self._doc.close()
        super().closeEvent(event)
