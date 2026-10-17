"""PDF viewer — real rendering via PyMuPDF with mouse text selection."""
from __future__ import annotations
import pymupdf as fitz
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QComboBox, QScrollArea, QFrame, QSizePolicy,
    QMessageBox
)
from PySide6.QtCore import Qt, Signal, QRect, QPoint
from PySide6.QtGui import QPainter, QColor, QPixmap, QPen, QCursor

from app.services.pdf_service import pdf_service

_TOOL_BTN_SS = (
    "QPushButton{background:transparent;border-radius:8px;"
    "color:#4A4E4A;font-size:14px;padding:4px;border:none;}"
    "QPushButton:hover{background:#EDD89A;color:#1A1C1A;}"
    "QPushButton:pressed{background:#D4C080;}"
)


# ── Toolbar ────────────────────────────────────────────────────────────────────

class PDFToolbar(QWidget):
    zoomChanged   = Signal(int)
    prevRequested = Signal()
    nextRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(48)
        self.setStyleSheet(
            "QWidget{background:#FFF8EC;"
            "border-top-left-radius:16px;border-top-right-radius:16px;}"
        )

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(2)

        def btn(text, tip, size=18):
            b = QPushButton(text)
            b.setFixedSize(32, 32)
            b.setCursor(Qt.PointingHandCursor)
            b.setToolTip(tip)
            b.setStyleSheet(_TOOL_BTN_SS.replace("font-size:14px", f"font-size:{size}px"))
            return b

        self.btn_prev = btn("‹", "Previous page")
        self.btn_next = btn("›", "Next page")

        self.page_input = QLineEdit("1")
        self.page_input.setFixedSize(38, 28)
        self.page_input.setAlignment(Qt.AlignCenter)
        self.page_input.setStyleSheet(
            "QLineEdit{background:#F7E7B5;border:1px solid #DDC880;"
            "border-radius:6px;color:#1A1C1A;font-size:13px;font-weight:600;}"
        )

        self.page_total = QLabel("/ 0")
        self.page_total.setStyleSheet(
            "color:#8A9A8A;font-size:13px;background:transparent;padding-left:4px;"
        )

        self.zoom_combo = QComboBox()
        self.zoom_combo.setFixedSize(80, 28)
        self.zoom_combo.setStyleSheet(
            "QComboBox{background:#F7E7B5;border:1px solid #DDC880;"
            "border-radius:6px;color:#1A1C1A;font-size:13px;font-weight:500;padding:0 8px;}"
            "QComboBox::drop-down{border:none;width:18px;}"
            "QComboBox::down-arrow{width:0;height:0;}"
            "QComboBox QAbstractItemView{background:#FFF8EC;border:1px solid #DDC880;"
            "border-radius:6px;color:#1A1C1A;selection-background-color:#F0C94C;}"
        )
        for lvl in [50, 75, 100, 125, 150, 175, 200]:
            self.zoom_combo.addItem(f"{lvl}%", lvl)
        self.zoom_combo.setCurrentText("125%")

        lay.addWidget(self.btn_prev)
        lay.addWidget(self.btn_next)
        lay.addSpacing(8)
        lay.addWidget(self.page_input)
        lay.addWidget(self.page_total)
        lay.addSpacing(10)
        lay.addWidget(self.zoom_combo)
        lay.addStretch()

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
            # parent PDFViewer handles the jump
            viewer = self.parent()
            if viewer and hasattr(viewer, "go_to_page"):
                viewer.go_to_page(page - 1)
        except ValueError:
            pass


# ── Page widget with selection ─────────────────────────────────────────────────

class PDFPageWidget(QLabel):
    """
    Displays a single rendered PDF page (QPixmap).
    Supports mouse-driven text selection with GemmaNotepad1 highlight overlay.
    Emits textSelected(text, page_num) on mouse release.
    """

    textSelected = Signal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.setStyleSheet("background:#FFF8EC;")
        self.setCursor(Qt.IBeamCursor)

        self._page_num   : int             = 0
        self._zoom       : float           = 1.25
        self._blocks     : list[dict]      = []   # [{text, rect}]
        self._sel_start  : QPoint | None   = None
        self._sel_rect   : QRect | None    = None
        self._sel_text   : str             = ""
        self._pixmap_orig: QPixmap | None  = None

    # ── Public ─────────────────────────────────────────────────────────────────

    def set_page(self, pixmap: QPixmap, blocks: list[dict],
                 page_num: int, zoom: float):
        self._pixmap_orig = pixmap
        self._blocks      = blocks
        self._page_num    = page_num
        self._zoom        = zoom
        self._sel_rect    = None
        self._sel_text    = ""
        self.setPixmap(pixmap)
        self.resize(pixmap.size())

    # ── Mouse events ───────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._sel_start = event.pos()
            self._sel_rect  = None
            self._sel_text  = ""
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

    # ── Paint selection overlay ────────────────────────────────────────────────

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._sel_rect and not self._sel_rect.isEmpty():
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)
            p.fillRect(self._sel_rect, QColor(240, 201, 76, 80))
            p.setPen(QPen(QColor(212, 160, 23, 180), 1))
            p.drawRect(self._sel_rect)
            p.end()

    # ── Text extraction ────────────────────────────────────────────────────────

    def _extract_selected_text(self) -> str:
        """Find all text blocks whose fitz.Rect overlaps the selection rect."""
        if not self._sel_rect or not self._blocks:
            return ""

        # Convert widget rect → PDF coordinates
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


# ── Main PDF viewer ────────────────────────────────────────────────────────────

class PDFViewer(QWidget):
    textSelected = Signal(str, int)   # (text, page_number 1-based)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("workspacePanel")
        self.setStyleSheet(
            "QWidget#workspacePanel{background:#FFF8EC;border-radius:16px;}"
        )

        self._doc         : fitz.Document | None = None
        self._current_page: int   = 0   # 0-based internally
        self._total_pages : int   = 0
        self._zoom        : float = 1.25
        self._doc_name    : str   = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.toolbar = PDFToolbar(self)
        root.addWidget(self.toolbar)

        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setFixedHeight(1)
        div.setStyleSheet("background:#EDD89A;")
        root.addWidget(div)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(False)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.scroll.setStyleSheet(
            "QScrollArea{background:#E8DDB0;border:none;"
            "border-bottom-left-radius:16px;border-bottom-right-radius:16px;}"
            "QScrollArea > QWidget{background:#E8DDB0;}"
        )

        self.page_widget = PDFPageWidget()
        self.page_widget.textSelected.connect(
            lambda t, p: self.textSelected.emit(t, p + 1)
        )
        # Enable mouse tracking so mouseMoveEvent fires without button held
        self.page_widget.setMouseTracking(True)
        self.scroll.setMouseTracking(True)
        self.scroll.viewport().setMouseTracking(True)
        self.scroll.setWidget(self.page_widget)
        root.addWidget(self.scroll, 1)

        self.toolbar.prevRequested.connect(self._prev)
        self.toolbar.nextRequested.connect(self._next)
        self.toolbar.zoomChanged.connect(self._on_zoom)

        # Show placeholder until a PDF is loaded
        self.page_widget.setText(
            "Open a PDF to start reading.\n\nUse the Upload button in the sidebar."
        )
        self.page_widget.setAlignment(Qt.AlignCenter)
        self.toolbar.update_display(0, 0)

    # ── Public API ─────────────────────────────────────────────────────────────

    def load_pdf(self, path: str, doc_name: str = ""):
        """Open a PDF file and render the first page."""
        try:
            if self._doc:
                self._doc.close()
            self._doc          = pdf_service.open(path)
            self._total_pages  = self._doc.page_count
            self._current_page = 0
            self._doc_name     = doc_name or path.split("/")[-1].split("\\")[-1]
            # Reset page widget style (remove placeholder text style)
            self.page_widget.setStyleSheet("background:#FFF8EC;")
            self.page_widget.setText("")
            self._render()
        except ValueError as e:
            QMessageBox.warning(self, "PDF too long", str(e))
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

    # ── Internal ───────────────────────────────────────────────────────────────

    def _render(self):
        if self._doc is None:
            return
        pixmap = pdf_service.render_page(self._doc, self._current_page, self._zoom)
        blocks = pdf_service.get_text_blocks(self._doc, self._current_page)
        self.page_widget.set_page(pixmap, blocks, self._current_page, self._zoom)
        self.toolbar.update_display(self._current_page + 1, self._total_pages)
        # Scroll back to top on page change
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

    def _show_placeholder(self):
        self.page_widget.setText(
            "Open a PDF to start reading.\n\nUse the Upload button in the sidebar."
        )
        self.page_widget.setAlignment(Qt.AlignCenter)
        self.page_widget.setStyleSheet("background:#FFF8EC; color:#8A9A8A; font-size:14px;")
        self.toolbar.update_display(0, 0)

    def closeEvent(self, event):
        if self._doc:
            self._doc.close()
        super().closeEvent(event)
