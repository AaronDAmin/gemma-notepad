"""Custom document tab bar — GemmaNotepad1 yellow strip at the top of the window."""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QFrame, QSizePolicy,
    QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor


class DocumentTab(QWidget):
    """Single tab: label + close button."""

    closeRequested = Signal(int)
    selected       = Signal(int)

    def __init__(self, tab_id: int, title: str, parent=None):
        super().__init__(parent)
        self.tab_id  = tab_id
        self._active = False

        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedHeight(34)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 8, 0)
        lay.setSpacing(8)

        self.label = QLabel(title)
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(16, 16)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.clicked.connect(lambda: self.closeRequested.emit(self.tab_id))

        lay.addWidget(self.label)
        lay.addWidget(self.close_btn)

        self.set_active(False)
        self.adjustSize()

    # ── Style helpers ──────────────────────────────────────────────────────────

    def set_active(self, active: bool):
        self._active = active
        if active:
            # Active tab: same GemmaNotepad1 as background → stands out via weight/text
            self.setStyleSheet(
                "QWidget{background:#F0C94C; border-radius:10px;}"
            )
            self.label.setStyleSheet(
                "color:#1A1C1A; font-size:13px; font-weight:600;"
                "background:transparent;"
            )
            self.close_btn.setStyleSheet(
                "QPushButton{background:transparent; color:#1A1C1A;"
                "font-size:10px; border:none; border-radius:4px;}"
                "QPushButton:hover{background:rgba(0,0,0,0.12);}"
            )
        else:
            # Inactive tab: dark charcoal pill on the GemmaNotepad1 strip
            self.setStyleSheet(
                "QWidget{background:#343834; border-radius:10px;}"
                "QWidget:hover{background:#3D413D;}"
            )
            self.label.setStyleSheet(
                "color:#B0B8B0; font-size:13px; font-weight:500;"
                "background:transparent;"
            )
            self.close_btn.setStyleSheet(
                "QPushButton{background:transparent; color:#6A7A6A;"
                "font-size:10px; border:none; border-radius:4px;}"
                "QPushButton:hover{background:rgba(255,255,255,0.08);"
                "color:#B0B8B0;}"
            )

    def set_title(self, title: str):
        self.label.setText(title)
        self.adjustSize()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.selected.emit(self.tab_id)
        super().mousePressEvent(event)


class TabBar(QWidget):
    """
    Full-width GemmaNotepad1 strip.  Active tab blends into the background;
    inactive tabs are dark charcoal pills.
    """

    tabSelected     = Signal(int)
    tabClosed       = Signal(int)
    newTabRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(52)
        self.setAutoFillBackground(True)  # ensure paintEvent fills the rect

        self._tabs: dict[int, DocumentTab] = {}
        self._active_id: int | None = None

        outer = QHBoxLayout(self)
        outer.setContentsMargins(12, 9, 12, 9)
        outer.setSpacing(0)

        # Scrollable area for tabs
        self._scroll = QScrollArea()
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setFixedHeight(34)
        self._scroll.setStyleSheet(
            "QScrollArea, QScrollArea > QWidget, "
            "QScrollArea > QWidget > QWidget {"
            "background: transparent; border: none;}"
        )

        self._tab_container = QWidget()
        self._tab_container.setStyleSheet("background: transparent;")
        self._tab_layout = QHBoxLayout(self._tab_container)
        self._tab_layout.setContentsMargins(0, 0, 0, 0)
        self._tab_layout.setSpacing(6)
        self._tab_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._tab_layout.addStretch()

        self._scroll.setWidget(self._tab_container)

        # + button — slightly darker GemmaNotepad1 so it reads as a button
        self.new_tab_btn = QPushButton("+")
        self.new_tab_btn.setFixedSize(34, 34)
        self.new_tab_btn.setCursor(Qt.PointingHandCursor)
        self.new_tab_btn.setStyleSheet(
            "QPushButton{background:#C89010; border-radius:10px;"
            "color:#1A1C1A; font-size:22px; font-weight:300; border:none;}"
            "QPushButton:hover{background:#B07800;}"
            "QPushButton:pressed{background:#906000;}"
        )
        self.new_tab_btn.clicked.connect(self.newTabRequested)

        outer.addWidget(self._scroll, 1)
        outer.addSpacing(8)
        outer.addWidget(self.new_tab_btn, 0, Qt.AlignVCenter)

    # ── Paint the GemmaNotepad1 background explicitly ────────────────────────────────
    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#F0C94C"))
        p.end()

    # ── Public API ─────────────────────────────────────────────────────────────

    def add_tab(self, tab_id: int, title: str, activate: bool = True):
        tab = DocumentTab(tab_id, title)
        tab.closeRequested.connect(self._on_close)
        tab.selected.connect(self._on_select)
        stretch_idx = self._tab_layout.count() - 1
        self._tab_layout.insertWidget(stretch_idx, tab)
        self._tabs[tab_id] = tab
        if activate:
            self._activate(tab_id)

    def remove_tab(self, tab_id: int):
        tab = self._tabs.pop(tab_id, None)
        if tab:
            self._tab_layout.removeWidget(tab)
            tab.deleteLater()
        if self._active_id == tab_id and self._tabs:
            self._activate(list(self._tabs.keys())[-1])

    def set_active_tab(self, tab_id: int):
        self._activate(tab_id)

    def rename_tab(self, tab_id: int, title: str):
        if tab_id in self._tabs:
            self._tabs[tab_id].set_title(title)

    def count(self) -> int:
        return len(self._tabs)

    def active_tab_id(self) -> int | None:
        return self._active_id

    # ── Internal ───────────────────────────────────────────────────────────────

    def _activate(self, tab_id: int):
        if self._active_id == tab_id:
            return
        if self._active_id in self._tabs:
            self._tabs[self._active_id].set_active(False)
        self._active_id = tab_id
        if tab_id in self._tabs:
            self._tabs[tab_id].set_active(True)
        self.tabSelected.emit(tab_id)

    def _on_close(self, tab_id: int):
        self.tabClosed.emit(tab_id)

    def _on_select(self, tab_id: int):
        self._activate(tab_id)
        self.tabSelected.emit(tab_id)
