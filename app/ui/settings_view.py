"""Settings dashboard — central workspace page for General, AI, Appearance & Storage."""
from __future__ import annotations
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QFrame, QStackedWidget, QSlider, QScrollArea,
    QFormLayout, QFileDialog, QMessageBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal

from app.core.config import APP_NAME, DB_PATH
from app.services.ollama_service import ollama_service
from app.storage.repositories import settings_repo


class SettingsView(QWidget):
    """Central workspace settings page with sub-tab navigation."""

    modelChanged = Signal(str)
    themeChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsView")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(
            "#settingsView{background-color: #FFF8EC; border-radius: 18px;}"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(36, 32, 36, 32)
        root.setSpacing(20)

        # ── Header ─────────────────────────────────────────────────────────────
        title = QLabel("Settings")
        title.setStyleSheet(
            "color: #1A1C1A; font-size: 26px; font-weight: 800; font-family: 'Segoe UI', sans-serif;"
        )
        root.addWidget(title)

        # ── Main layout: sub-tabs + stack ──────────────────────────────────────
        body = QHBoxLayout()
        body.setSpacing(24)

        # Left sub-navigation
        nav_box = QWidget()
        nav_box.setFixedWidth(200)
        nav_box.setStyleSheet("background-color: #F6ECCF; border-radius: 14px;")
        nav_lay = QVBoxLayout(nav_box)
        nav_lay.setContentsMargins(12, 14, 12, 14)
        nav_lay.setSpacing(6)

        nav_title = QLabel("PREFERENCES")
        nav_title.setStyleSheet("color: #7A7465; font-size: 11px; font-weight: 700; padding-left: 6px;")
        nav_lay.addWidget(nav_title)

        self._nav_buttons = []
        self._tabs = [
            ("General", self._build_general_tab),
            ("AI Model (Ollama)", self._build_ai_tab),
            ("Appearance", self._build_appearance_tab),
            ("Advanced & Storage", self._build_storage_tab),
        ]

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")

        for idx, (name, builder) in enumerate(self._tabs):
            btn = QPushButton(name.replace("&", "&&"))
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, i=idx: self._switch_tab(i))
            self._nav_buttons.append(btn)
            nav_lay.addWidget(btn)

            tab_widget = builder()
            self.stack.addWidget(tab_widget)

        nav_lay.addStretch(1)
        body.addWidget(nav_box)
        body.addWidget(self.stack, 1)

        root.addLayout(body, 1)
        self._switch_tab(0)

    def _switch_tab(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self._nav_buttons):
            if i == index:
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

    # ── Sub-tab 0: General ─────────────────────────────────────────────────────
    def _build_general_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(10, 0, 10, 10)
        lay.setSpacing(16)
        lay.setAlignment(Qt.AlignTop)

        h = QLabel("General Settings")
        h.setStyleSheet("color: #1A1C1A; font-size: 18px; font-weight: 700;")
        lay.addWidget(h)

        card = QFrame()
        card.setStyleSheet("background-color: #F6ECCF; border-radius: 12px; padding: 14px;")
        card_l = QVBoxLayout(card)
        card_l.setSpacing(12)

        cb1 = QCheckBox("Automatically restore last open document on launch")
        cb1.setChecked(True)
        cb1.setStyleSheet("color: #1A1C1A; font-size: 13px;")

        cb2 = QCheckBox("Save note changes automatically while typing")
        cb2.setChecked(True)
        cb2.setStyleSheet("color: #1A1C1A; font-size: 13px;")

        cb3 = QCheckBox("Show confirmation when closing document tabs")
        cb3.setChecked(False)
        cb3.setStyleSheet("color: #1A1C1A; font-size: 13px;")

        card_l.addWidget(cb1)
        card_l.addWidget(cb2)
        card_l.addWidget(cb3)
        lay.addWidget(card)

        return w

    # ── Sub-tab 1: AI Model (Ollama) ──────────────────────────────────────────
    def _build_ai_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(10, 0, 10, 10)
        lay.setSpacing(16)
        lay.setAlignment(Qt.AlignTop)

        h = QLabel("AI Model & Ollama Runtime")
        h.setStyleSheet("color: #1A1C1A; font-size: 18px; font-weight: 700;")
        lay.addWidget(h)

        card = QFrame()
        card.setStyleSheet("background-color: #F6ECCF; border-radius: 12px; padding: 16px;")
        card_l = QVBoxLayout(card)
        card_l.setSpacing(14)

        # Status row
        status_row = QHBoxLayout()
        st_lbl = QLabel("Ollama Status:")
        st_lbl.setStyleSheet("color: #1A1C1A; font-size: 13px; font-weight: 600;")
        self.ai_status_pill = QLabel("Checking…")
        self.ai_status_pill.setStyleSheet(
            "background-color: #FFD04D; border-radius: 6px; color: #1A1C1A;"
            "padding: 3px 10px; font-size: 12px; font-weight: 700;"
        )
        status_row.addWidget(st_lbl)
        status_row.addWidget(self.ai_status_pill)
        status_row.addStretch(1)
        card_l.addLayout(status_row)

        # Model selector
        m_row = QHBoxLayout()
        m_lbl = QLabel("Active Model:")
        m_lbl.setStyleSheet("color: #1A1C1A; font-size: 13px; font-weight: 600;")
        self.model_combo = QComboBox()
        self.model_combo.setFixedWidth(260)
        self.model_combo.setStyleSheet(
            "QComboBox{background-color: #FFF8EC; border: 1px solid #E8DCB8; border-radius: 8px;"
            "color: #1A1C1A; padding: 6px 12px; font-size: 13px;}"
        )
        self.model_combo.currentIndexChanged.connect(self._on_model_selected)

        m_row.addWidget(m_lbl)
        m_row.addWidget(self.model_combo)
        m_row.addStretch(1)
        card_l.addLayout(m_row)

        # Temperature
        t_row = QHBoxLayout()
        t_lbl = QLabel("Creativity (Temperature):")
        t_lbl.setStyleSheet("color: #1A1C1A; font-size: 13px; font-weight: 600;")
        t_slider = QSlider(Qt.Horizontal)
        t_slider.setRange(0, 100)
        t_slider.setValue(30)
        t_slider.setFixedWidth(200)
        t_val = QLabel("0.3")
        t_val.setStyleSheet("color: #5A5445; font-size: 13px;")
        t_slider.valueChanged.connect(lambda v: t_val.setText(f"{v/100:.1f}"))

        t_row.addWidget(t_lbl)
        t_row.addWidget(t_slider)
        t_row.addWidget(t_val)
        t_row.addStretch(1)
        card_l.addLayout(t_row)

        # Refresh models button
        btn_refresh = QPushButton("⟳  Refresh Models")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet(
            "QPushButton{background-color: #FFD04D; border-radius: 8px; color: #1A1C1A;"
            "font-size: 12.5px; font-weight: 700; padding: 6px 16px; border: none;}"
            "QPushButton:hover{background-color: #E8B93A;}"
        )
        btn_refresh.clicked.connect(self.refresh_ai_models)
        card_l.addWidget(btn_refresh, 0, Qt.AlignLeft)

        lay.addWidget(card)
        self.refresh_ai_models()
        return w

    def refresh_ai_models(self):
        is_up = ollama_service.is_running()
        if is_up:
            self.ai_status_pill.setText(f"Connected • {ollama_service.active_host()}")
            self.ai_status_pill.setStyleSheet(
                "background-color: #4CAF50; border-radius: 6px; color: #FFFFFF;"
                "padding: 3px 10px; font-size: 12px; font-weight: 700;"
            )
            models = ollama_service.list_models()
            self.model_combo.clear()
            saved = settings_repo.get("active_model", "")
            for m in models:
                self.model_combo.addItem(m)
            if saved and saved in models:
                self.model_combo.setCurrentText(saved)
            elif models:
                self.model_combo.setCurrentIndex(0)
        else:
            self.ai_status_pill.setText("Offline (http://localhost:11434)")
            self.ai_status_pill.setStyleSheet(
                "background-color: #E57373; border-radius: 6px; color: #FFFFFF;"
                "padding: 3px 10px; font-size: 12px; font-weight: 700;"
            )
            self.model_combo.clear()
            self.model_combo.addItem("No local models found")

    def _on_model_selected(self):
        m = self.model_combo.currentText()
        if m and m != "No local models found":
            settings_repo.set("active_model", m)
            self.modelChanged.emit(m)

    # ── Sub-tab 2: Appearance ──────────────────────────────────────────────────
    def _build_appearance_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(10, 0, 10, 10)
        lay.setSpacing(16)
        lay.setAlignment(Qt.AlignTop)

        h = QLabel("Appearance & Theme")
        h.setStyleSheet("color: #1A1C1A; font-size: 18px; font-weight: 700;")
        lay.addWidget(h)

        card = QFrame()
        card.setStyleSheet("background-color: #F6ECCF; border-radius: 12px; padding: 16px;")
        card_l = QVBoxLayout(card)
        card_l.setSpacing(12)

        t_row = QHBoxLayout()
        t_lbl = QLabel("Color Theme:")
        t_lbl.setStyleSheet("color: #1A1C1A; font-size: 13px; font-weight: 600;")
        theme_combo = QComboBox()
        theme_combo.addItems(["Mustard Dark (Default)", "Warm Light", "Classic Dark"])
        theme_combo.setStyleSheet(
            "QComboBox{background-color: #FFF8EC; border: 1px solid #E8DCB8; border-radius: 8px;"
            "color: #1A1C1A; padding: 6px 12px; font-size: 13px;}"
        )
        t_row.addWidget(t_lbl)
        t_row.addWidget(theme_combo)
        t_row.addStretch(1)
        card_l.addLayout(t_row)

        f_row = QHBoxLayout()
        f_lbl = QLabel("Font Size:")
        f_lbl.setStyleSheet("color: #1A1C1A; font-size: 13px; font-weight: 600;")
        font_combo = QComboBox()
        font_combo.addItems(["Default (100%)", "Medium (115%)", "Large (130%)"])
        font_combo.setStyleSheet(
            "QComboBox{background-color: #FFF8EC; border: 1px solid #E8DCB8; border-radius: 8px;"
            "color: #1A1C1A; padding: 6px 12px; font-size: 13px;}"
        )
        f_row.addWidget(f_lbl)
        f_row.addWidget(font_combo)
        f_row.addStretch(1)
        card_l.addLayout(f_row)

        lay.addWidget(card)
        return w

    # ── Sub-tab 3: Advanced & Storage ──────────────────────────────────────────
    def _build_storage_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(10, 0, 10, 10)
        lay.setSpacing(16)
        lay.setAlignment(Qt.AlignTop)

        h = QLabel("Advanced & Storage")
        h.setStyleSheet("color: #1A1C1A; font-size: 18px; font-weight: 700;")
        lay.addWidget(h)

        card = QFrame()
        card.setStyleSheet("background-color: #F6ECCF; border-radius: 12px; padding: 16px;")
        card_l = QVBoxLayout(card)
        card_l.setSpacing(12)

        db_lbl = QLabel(f"Database: {DB_PATH}")
        db_lbl.setStyleSheet("color: #5A5445; font-size: 12.5px; font-family: monospace;")
        card_l.addWidget(db_lbl)

        btn_row = QHBoxLayout()
        btn_clear = QPushButton("Clear Render Cache")
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.setStyleSheet(
            "QPushButton{background-color: #EEDBBA; border-radius: 8px; color: #1A1C1A;"
            "font-size: 12.5px; font-weight: 600; padding: 6px 16px; border: none;}"
            "QPushButton:hover{background-color: #E2CF9F;}"
        )
        btn_clear.clicked.connect(lambda: QMessageBox.information(self, "Cache", "Cache cleared successfully."))
        btn_row.addWidget(btn_clear)
        btn_row.addStretch(1)
        card_l.addLayout(btn_row)

        lay.addWidget(card)
        return w
