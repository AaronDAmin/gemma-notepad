"""Image viewer widget — displays an imported image with zoom, rotation, and pan."""
from __future__ import annotations
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel, QFrame, QHBoxLayout,
    QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, QPoint
from PySide6.QtGui import QPixmap, QTransform, QCursor

from app.ui.icons import load_svg_pixmap


class ImageViewer(QWidget):
    """
    Displays an image file inside a scrollable, zoomable, and rotatable area.
    Follows the mustard & cream design language with rich toolbar controls.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("imageViewer")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(
            "#imageViewer{background-color: #FFF8EC; border-radius: 18px;}"
        )

        self._pixmap: QPixmap | None = None
        self._current_path: str = ""
        self._zoom: float = 1.0
        self._rotation: int = 0
        self._drag_start_pos: QPoint | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Toolbar ────────────────────────────────────────────────────────────
        toolbar = QWidget()
        toolbar.setFixedHeight(48)
        toolbar.setStyleSheet(
            "background-color: #FFF8EC; border-bottom: 1px solid #EDD89A;"
            "border-top-left-radius: 18px; border-top-right-radius: 18px;"
        )
        t_layout = QHBoxLayout(toolbar)
        t_layout.setContentsMargins(18, 0, 18, 0)
        t_layout.setSpacing(8)

        # Image badge
        icon_box = QFrame()
        icon_box.setFixedSize(28, 28)
        icon_box.setStyleSheet("background-color: #F6ECCF; border-radius: 6px;")
        ib_lay = QVBoxLayout(icon_box)
        ib_lay.setContentsMargins(0, 0, 0, 0)
        ib_lay.setAlignment(Qt.AlignCenter)
        ib_lbl = QLabel()
        ib_lbl.setPixmap(load_svg_pixmap("image_card_icon.svg", 16, color="#1A1C1A"))
        ib_lay.addWidget(ib_lbl)
        t_layout.addWidget(icon_box)

        # Title / Filename
        self.filename_lbl = QLabel("No image loaded")
        self.filename_lbl.setStyleSheet(
            "color: #1A1C1A; font-size: 13.5px; font-weight: 600; background: transparent;"
        )
        t_layout.addWidget(self.filename_lbl)

        sep1 = self._separator()
        t_layout.addWidget(sep1)

        t_layout.addStretch(1)

        # Zoom controls
        self.zoom_out_btn = self._tool_btn("－", "Zoom out")
        self.zoom_in_btn  = self._tool_btn("＋", "Zoom in")

        self.zoom_pill = QLabel("100%")
        self.zoom_pill.setFixedHeight(26)
        self.zoom_pill.setAlignment(Qt.AlignCenter)
        self.zoom_pill.setStyleSheet(
            "QLabel{background-color: #F6ECCF; border: 1px solid #E8DCB8; border-radius: 6px;"
            "color: #1A1C1A; font-size: 12px; font-weight: 600; padding: 0 8px;}"
        )

        t_layout.addWidget(self.zoom_out_btn)
        t_layout.addWidget(self.zoom_pill)
        t_layout.addWidget(self.zoom_in_btn)

        sep2 = self._separator()
        t_layout.addWidget(sep2)

        # View and rotation tools
        self.fit_btn = self._tool_btn("⊡", "Fit to window")
        self.rotate_left_btn  = self._tool_btn("↶", "Rotate left 90°")
        self.rotate_right_btn = self._tool_btn("↷", "Rotate right 90°")

        t_layout.addWidget(self.fit_btn)
        t_layout.addWidget(self.rotate_left_btn)
        t_layout.addWidget(self.rotate_right_btn)

        sep3 = self._separator()
        t_layout.addWidget(sep3)

        self.btn_bookmark = self._tool_btn("🔖", "Bookmark diagram")
        self.btn_more     = self._tool_btn("⋮", "Options")
        t_layout.addWidget(self.btn_bookmark)
        t_layout.addWidget(self.btn_more)

        root.addWidget(toolbar)

        # ── Scroll Area ────────────────────────────────────────────────────────
        self.scroll = QScrollArea()
        self.scroll.setObjectName("imageScrollArea")
        self.scroll.setWidgetResizable(False)
        self.scroll.setAlignment(Qt.AlignCenter)
        self.scroll.setStyleSheet(
            "QScrollArea{background-color: #FCF6EC; border: none;"
            "border-bottom-left-radius: 18px; border-bottom-right-radius: 18px;}"
            "QScrollArea > QWidget{background-color: #FCF6EC;}"
        )
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setStyleSheet("background: transparent;")
        self.img_label.setText("No image loaded")
        self.img_label.setCursor(Qt.OpenHandCursor)

        self.scroll.setWidget(self.img_label)
        root.addWidget(self.scroll, 1)

        # ── Signal wiring ──────────────────────────────────────────────────────
        self.zoom_in_btn.clicked.connect(self._zoom_in)
        self.zoom_out_btn.clicked.connect(self._zoom_out)
        self.fit_btn.clicked.connect(self.fit_to_window)
        self.rotate_left_btn.clicked.connect(self.rotate_left)
        self.rotate_right_btn.clicked.connect(self.rotate_right)

        # Mouse panning on scroll area
        self.img_label.mousePressEvent = self._on_mouse_press
        self.img_label.mouseMoveEvent = self._on_mouse_move
        self.img_label.mouseReleaseEvent = self._on_mouse_release

    def _separator(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedWidth(1)
        sep.setFixedHeight(18)
        sep.setStyleSheet("background-color: #EDD89A;")
        return sep

    def _tool_btn(self, text: str, tip: str) -> QPushButton:
        b = QPushButton(text)
        b.setFixedSize(28, 28)
        b.setCursor(Qt.PointingHandCursor)
        b.setToolTip(tip)
        b.setStyleSheet(
            "QPushButton{background-color: transparent; border: none; border-radius: 6px;"
            "color: #1A1C1A; font-size: 14px; font-weight: 600;}"
            "QPushButton:hover{background-color: #EEDBBA;}"
            "QPushButton:pressed{background-color: #DDC8A0;}"
        )
        return b

    # ── Pan & Drag ─────────────────────────────────────────────────────────────

    def _on_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self.img_label.setCursor(Qt.ClosedHandCursor)
            self._drag_start_pos = event.globalPosition().toPoint()
        event.accept()

    def _on_mouse_move(self, event):
        if self._drag_start_pos is not None:
            delta = event.globalPosition().toPoint() - self._drag_start_pos
            self._drag_start_pos = event.globalPosition().toPoint()
            self.scroll.horizontalScrollBar().setValue(
                self.scroll.horizontalScrollBar().value() - delta.x()
            )
            self.scroll.verticalScrollBar().setValue(
                self.scroll.verticalScrollBar().value() - delta.y()
            )
        event.accept()

    def _on_mouse_release(self, event):
        self._drag_start_pos = None
        self.img_label.setCursor(Qt.OpenHandCursor)
        event.accept()

    def wheelEvent(self, event):
        # Zoom on wheel
        if event.angleDelta().y() > 0:
            self._zoom_in()
        else:
            self._zoom_out()
        event.accept()

    # ── Public API ─────────────────────────────────────────────────────────────

    def load_image(self, path: str):
        pix = QPixmap(path)
        if pix.isNull():
            self.img_label.setText(f"Could not load: {path}")
            return
        self._current_path = path
        self._pixmap = pix
        self._zoom = 1.0
        self._rotation = 0
        self.filename_lbl.setText(os.path.basename(path))
        self.fit_to_window()

    def rotate_left(self):
        self._rotation = (self._rotation - 90) % 360
        self._render()

    def rotate_right(self):
        self._rotation = (self._rotation + 90) % 360
        self._render()

    def fit_to_window(self):
        if self._pixmap is None:
            return
        area_size = self.scroll.viewport().size()
        pw = self._pixmap.width()
        ph = self._pixmap.height()
        if self._rotation in (90, 270):
            pw, ph = ph, pw

        scale_w = (area_size.width() - 40) / max(pw, 1)
        scale_h = (area_size.height() - 40) / max(ph, 1)
        self._zoom = min(scale_w, scale_h, 1.0)
        self._render()

    def _zoom_in(self):
        self._zoom = min(self._zoom * 1.25, 5.0)
        self._render()

    def _zoom_out(self):
        self._zoom = max(self._zoom / 1.25, 0.1)
        self._render()

    def _render(self):
        if self._pixmap is None:
            return

        transform = QTransform()
        if self._rotation:
            transform.rotate(self._rotation)

        rotated = self._pixmap.transformed(transform, Qt.SmoothTransformation)
        w = int(rotated.width()  * self._zoom)
        h = int(rotated.height() * self._zoom)

        scaled = rotated.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.img_label.setPixmap(scaled)
        self.img_label.resize(scaled.size())
        self.zoom_pill.setText(f"{int(self._zoom * 100)}%")
