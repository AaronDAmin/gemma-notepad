"""Image viewer widget — displays an imported image with zoom/scroll.
Phase 1: UI shell; Phase 2 will load real images.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel, QFrame, QHBoxLayout,
    QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap


class ImageViewer(QWidget):
    """Displays an image file inside a scrollable, zoomable area."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("workspacePanel")

        self._pixmap: QPixmap | None = None
        self._zoom = 1.0

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Mini toolbar ───────────────────────────────────────────────────────
        toolbar = QWidget()
        toolbar.setFixedHeight(48)
        toolbar.setStyleSheet(
            "background:#FFF8EC; border-bottom:1px solid #EDD89A;"
            "border-top-left-radius:16px; border-top-right-radius:16px;"
        )
        t_layout = QHBoxLayout(toolbar)
        t_layout.setContentsMargins(14, 0, 14, 0)
        t_layout.setSpacing(6)

        self.zoom_in_btn  = self._tool_btn("＋", "Zoom in")
        self.zoom_out_btn = self._tool_btn("－", "Zoom out")
        self.fit_btn      = self._tool_btn("⊡", "Fit to window")
        self.zoom_label   = QLabel("100%")
        self.zoom_label.setStyleSheet(
            "color:#4A4E4A; font-size:13px; background:transparent;"
        )

        t_layout.addWidget(self.zoom_out_btn)
        t_layout.addWidget(self.zoom_label)
        t_layout.addWidget(self.zoom_in_btn)
        t_layout.addWidget(self.fit_btn)
        t_layout.addStretch()

        root.addWidget(toolbar)

        # ── Scroll area ────────────────────────────────────────────────────────
        self.scroll = QScrollArea()
        self.scroll.setObjectName("imageScrollArea")
        self.scroll.setWidgetResizable(False)
        self.scroll.setAlignment(Qt.AlignCenter)
        self.scroll.setStyleSheet(
            "QScrollArea{background:#F7E7B5; border:none;"
            "border-bottom-left-radius:16px; border-bottom-right-radius:16px;}"
        )
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setStyleSheet("background:#F7E7B5;")
        self.img_label.setText("No image loaded")
        self.scroll.setWidget(self.img_label)

        root.addWidget(self.scroll, 1)

        # ── Wire ───────────────────────────────────────────────────────────────
        self.zoom_in_btn.clicked.connect(self._zoom_in)
        self.zoom_out_btn.clicked.connect(self._zoom_out)
        self.fit_btn.clicked.connect(self._fit)

    def _tool_btn(self, icon: str, tip: str) -> QPushButton:
        b = QPushButton(icon)
        b.setObjectName("pdfToolBtn")
        b.setFixedSize(30, 30)
        b.setCursor(Qt.PointingHandCursor)
        b.setToolTip(tip)
        return b

    # ── Public API ─────────────────────────────────────────────────────────────

    def load_image(self, path: str):
        pix = QPixmap(path)
        if pix.isNull():
            self.img_label.setText(f"Could not load: {path}")
            return
        self._pixmap = pix
        self._zoom = 1.0
        self._render()

    def _render(self):
        if self._pixmap is None:
            return
        w = int(self._pixmap.width()  * self._zoom)
        h = int(self._pixmap.height() * self._zoom)
        scaled = self._pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.img_label.setPixmap(scaled)
        self.img_label.resize(scaled.size())
        self.zoom_label.setText(f"{int(self._zoom * 100)}%")

    def _zoom_in(self):
        self._zoom = min(self._zoom * 1.2, 4.0)
        self._render()

    def _zoom_out(self):
        self._zoom = max(self._zoom / 1.2, 0.1)
        self._render()

    def _fit(self):
        if self._pixmap is None:
            return
        area_size = self.scroll.viewport().size()
        scale_w = area_size.width()  / self._pixmap.width()
        scale_h = area_size.height() / self._pixmap.height()
        self._zoom = min(scale_w, scale_h)
        self._render()
