"""Custom document tab bar and unified title bar."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QFrame, QSizePolicy,
    QScrollArea
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QPainter, QColor


class TrafficLights(QWidget):
    """Mac-style traffic light dots at top left."""

    closeClicked    = Signal()
    minimizeClicked = Signal()
    maximizeClicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(68, 28)
        self.setAttribute(Qt.WA_Hover, True)
        self.setCursor(Qt.ArrowCursor)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 0, 4, 0)
        lay.setSpacing(8)
        lay.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        def make_dot(color: str, hover_color: str, click_signal):
            btn = QPushButton()
            btn.setFixedSize(12, 12)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(
                f"QPushButton{{background-color:{color};border-radius:6px;border:none;}}"
                f"QPushButton:hover{{background-color:{hover_color};}}"
            )
            btn.clicked.connect(click_signal)
            return btn

        self.btn_close = make_dot("#ED6A5E", "#FF5442", self.closeClicked)
        self.btn_min   = make_dot("#F4BF4F", "#FFB703", self.minimizeClicked)
        self.btn_max   = make_dot("#61C554", "#4CAF50", self.maximizeClicked)

        lay.addWidget(self.btn_close)
        lay.addWidget(self.btn_min)
        lay.addWidget(self.btn_max)


class WindowControls(QWidget):
    """Windows-style minimize / maximize / close buttons at top right."""

    minimizeClicked = Signal()
    maximizeClicked = Signal()
    closeClicked    = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(32)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 4, 0)
        lay.setSpacing(2)
        lay.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        def btn(text: str, is_close: bool = False):
            b = QPushButton(text)
            b.setFixedSize(32, 28)
            b.setCursor(Qt.PointingHandCursor)
            hover_bg = "#E05555" if is_close else "rgba(255, 255, 255, 0.08)"
            hover_color = "#FFFFFF" if is_close else "#F0EDE8"
            b.setStyleSheet(
                f"QPushButton{{background:transparent;color:#A0ACA0;font-size:13px;"
                f"border:none;border-radius:6px;font-family:'Segoe UI',sans-serif;}}"
                f"QPushButton:hover{{background:{hover_bg};color:{hover_color};}}"
            )
            return b

        self.btn_min   = btn("—")
        self.btn_max   = btn("□")
        self.btn_close = btn("✕", is_close=True)

        self.btn_min.clicked.connect(self.minimizeClicked)
        self.btn_max.clicked.connect(self.maximizeClicked)
        self.btn_close.clicked.connect(self.closeClicked)

        lay.addWidget(self.btn_min)
        lay.addWidget(self.btn_max)
        lay.addWidget(self.btn_close)


class DocumentTab(QWidget):
    """Single document tab (active or inactive)."""

    closeRequested = Signal(int)
    selected       = Signal(int)

    def __init__(self, tab_id: int, title: str, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.tab_id  = tab_id
        self._active = False

        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(44)
        self.setMinimumWidth(115)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 10, 0)
        lay.setSpacing(10)
        lay.setAlignment(Qt.AlignVCenter)

        self.label = QLabel(title)
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(18, 18)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.clicked.connect(lambda: self.closeRequested.emit(self.tab_id))

        lay.addWidget(self.label)
        lay.addWidget(self.close_btn)

        self.set_active(False)

    def set_active(self, active: bool):
        self._active = active
        if active:
            # Active tab: warm yellow, rounded top, joins workspace
            self.setStyleSheet(
                "QWidget{"
                "background-color: #FFD04D;"
                "border-top-left-radius: 12px;"
                "border-top-right-radius: 12px;"
                "border-bottom-left-radius: 0px;"
                "border-bottom-right-radius: 0px;"
                "}"
            )
            self.label.setStyleSheet(
                "color: #1A1C1A; font-size: 13.5px; font-weight: 700; background: transparent;"
            )
            self.close_btn.setStyleSheet(
                "QPushButton{background: transparent; color: #1A1C1A; font-size: 11px; font-weight: 600; border: none; border-radius: 4px;}"
                "QPushButton:hover{background: rgba(0, 0, 0, 0.14);}"
            )
        else:
            # Inactive tab: dark charcoal pill
            self.setStyleSheet(
                "QWidget{"
                "background-color: #363C38;"
                "border-radius: 10px;"
                "}"
                "QWidget:hover{background-color: #3F4742;}"
            )
            self.label.setStyleSheet(
                "color: #FFF1CC; font-size: 13px; font-weight: 500; background: transparent;"
            )
            self.close_btn.setStyleSheet(
                "QPushButton{background: transparent; color: #8A9A8A; font-size: 10px; border: none; border-radius: 4px;}"
                "QPushButton:hover{background: rgba(255, 255, 255, 0.12); color: #FFF1CC;}"
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
    Unified titlebar & document tab strip:
      Left   — Traffic lights (red, yellow, green)
      Middle — Tabs + '+' button
      Right  — Window controls (—, □, ✕)
    """

    tabSelected     = Signal(int)
    tabClosed       = Signal(int)
    newTabRequested = Signal()

    minimizeRequested = Signal()
    maximizeRequested = Signal()
    closeRequested    = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(56)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("QWidget{background-color: #202A27;}")

        self._tabs: dict[int, DocumentTab] = {}
        self._active_id: int | None = None
        self._drag_pos: QPoint | None = None

        outer = QHBoxLayout(self)
        outer.setContentsMargins(14, 8, 12, 0)
        outer.setSpacing(12)
        outer.setAlignment(Qt.AlignBottom)

        # ── Traffic lights on far left ─────────────────────────────────────────
        self.traffic_lights = TrafficLights()
        self.traffic_lights.closeClicked.connect(self.closeRequested)
        self.traffic_lights.minimizeClicked.connect(self.minimizeRequested)
        self.traffic_lights.maximizeClicked.connect(self.maximizeRequested)
        outer.addWidget(self.traffic_lights, 0, Qt.AlignVCenter)
        outer.addSpacing(16)

        # ── Tabs scroll area ───────────────────────────────────────────────────
        self._tab_container = QWidget()
        self._tab_container.setStyleSheet("background: transparent;")
        self._tab_layout = QHBoxLayout(self._tab_container)
        self._tab_layout.setContentsMargins(0, 0, 0, 0)
        self._tab_layout.setSpacing(8)
        self._tab_layout.setAlignment(Qt.AlignLeft | Qt.AlignBottom)

        outer.addWidget(self._tab_container, 0, Qt.AlignBottom)

        # ── '+' New tab button ─────────────────────────────────────────────────
        self.new_tab_btn = QPushButton("+")
        self.new_tab_btn.setFixedSize(36, 36)
        self.new_tab_btn.setCursor(Qt.PointingHandCursor)
        self.new_tab_btn.setStyleSheet(
            "QPushButton{"
            "background-color: #FFD04D;"
            "border-radius: 10px;"
            "color: #1A1C1A;"
            "font-size: 20px;"
            "font-weight: 400;"
            "border: none;"
            "}"
            "QPushButton:hover{background-color: #E8B93A;}"
            "QPushButton:pressed{background-color: #D4A017;}"
        )
        self.new_tab_btn.clicked.connect(self.newTabRequested)
        outer.addWidget(self.new_tab_btn, 0, Qt.AlignVCenter)

        outer.addStretch(1)

        # ── Window controls on far right ───────────────────────────────────────
        self.win_controls = WindowControls()
        self.win_controls.minimizeClicked.connect(self.minimizeRequested)
        self.win_controls.maximizeClicked.connect(self.maximizeRequested)
        self.win_controls.closeClicked.connect(self.closeRequested)
        outer.addWidget(self.win_controls, 0, Qt.AlignVCenter)

    # ── Window Dragging ────────────────────────────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            win = self.window()
            if win:
                self._drag_pos = event.globalPosition().toPoint() - win.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.LeftButton:
            win = self.window()
            if win and not win.isMaximized():
                win.move(event.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.maximizeRequested.emit()
        super().mouseDoubleClickEvent(event)

    # ── Tab Management ─────────────────────────────────────────────────────────
    def add_tab(self, tab_id: int, title: str, activate: bool = True):
        tab = DocumentTab(tab_id, title)
        tab.closeRequested.connect(self._on_close)
        tab.selected.connect(self._on_select)
        self._tab_layout.addWidget(tab)
        self._tabs[tab_id] = tab
        if activate:
            self._activate(tab_id)

    def remove_tab(self, tab_id: int):
        tab = self._tabs.pop(tab_id, None)
        if tab:
            self._tab_layout.removeWidget(tab)
            tab.deleteLater()
        if not self._tabs:
            self._active_id = None
        elif self._active_id == tab_id and self._tabs:
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
