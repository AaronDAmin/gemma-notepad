"""AI contextual popup — explains selected text using a local Ollama model."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFrame, QScrollArea, QLineEdit, QGraphicsDropShadowEffect,
    QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QPoint, QTimer
from PySide6.QtGui import QColor

from app.services.context_service import context_service
from app.workers.ai_worker import AIWorker


class AIContextPopup(QWidget):
    """
    Floating popup shown when text is selected.
    States:
      idle     → two action buttons
      loading  → spinner label
      result   → scrollable explanation + follow-up field
      error    → error message
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # No separate window flags — stays a child widget floating over the parent
        # This works correctly on both Windows and Linux/Wayland
        self.setFixedWidth(360)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(
            "AIContextPopup{"
            "background:#282B28;"
            "border-radius:14px;"
            "border:1px solid #3D413D;"
            "}"
        )
        # Raise above siblings
        self.raise_()

        self._model        : str           = ""
        self._selected_text: str           = ""
        self._context      : str           = ""
        self._doc_name     : str           = ""
        self._worker       : AIWorker | None = None

        # ── Root layout ────────────────────────────────────────────────────────
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(0, 0, 0, 0)
        self._root.setSpacing(0)

        # ── Action bar (idle state) ────────────────────────────────────────────
        self._action_bar = QWidget()
        self._action_bar.setStyleSheet("background:transparent;")
        ab_lay = QHBoxLayout(self._action_bar)
        ab_lay.setContentsMargins(6, 4, 6, 4)
        ab_lay.setSpacing(0)

        self._btn_explain = self._action_btn("✦  Explain with AI")
        self._btn_ask     = self._action_btn("⊙  Ask a question")

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedWidth(1)
        sep.setStyleSheet("background:#3D413D;margin:6px 2px;")

        self._btn_close_idle = QPushButton("✕")
        self._btn_close_idle.setFixedSize(28, 28)
        self._btn_close_idle.setCursor(Qt.PointingHandCursor)
        self._btn_close_idle.setStyleSheet(
            "QPushButton{background:transparent;color:#6A7A6A;"
            "font-size:12px;border:none;border-radius:6px;}"
            "QPushButton:hover{background:#343834;color:#F0EDE8;}"
        )

        ab_lay.addWidget(self._btn_explain)
        ab_lay.addWidget(sep)
        ab_lay.addWidget(self._btn_ask)
        ab_lay.addStretch()
        ab_lay.addWidget(self._btn_close_idle)

        # ── Expanded panel (loading / result / error) ──────────────────────────
        self._expanded = QWidget()
        self._expanded.setStyleSheet(
            "QWidget{background:transparent;border:none;}"
        )
        self._expanded.hide()
        exp_lay = QVBoxLayout(self._expanded)
        exp_lay.setContentsMargins(14, 10, 14, 14)
        exp_lay.setSpacing(8)

        # Close button at top-right
        close_row = QHBoxLayout()
        close_row.addStretch()
        self._btn_close_exp = QPushButton("✕")
        self._btn_close_exp.setFixedSize(24, 24)
        self._btn_close_exp.setCursor(Qt.PointingHandCursor)
        self._btn_close_exp.setStyleSheet(
            "QPushButton{background:transparent;color:#6A7A6A;"
            "font-size:11px;border:none;border-radius:5px;}"
            "QPushButton:hover{background:#343834;color:#F0EDE8;}"
        )
        close_row.addWidget(self._btn_close_exp)
        exp_lay.addLayout(close_row)

        # Spinner / status label
        self._status_lbl = QLabel("⟳  Generating…")
        self._status_lbl.setStyleSheet(
            "color:#D4A017;font-size:13px;background:transparent;font-weight:600;"
        )
        self._status_lbl.setAlignment(Qt.AlignCenter)
        exp_lay.addWidget(self._status_lbl)

        # Result scroll area
        self._result_scroll = QScrollArea()
        self._result_scroll.setWidgetResizable(True)
        self._result_scroll.setFixedHeight(220)
        self._result_scroll.setFrameShape(QFrame.NoFrame)
        self._result_scroll.setStyleSheet(
            "QScrollArea{background:#1E211E;border-radius:8px;border:none;}"
            "QScrollArea > QWidget{background:#1E211E;}"
        )
        self._result_scroll.hide()

        self._result_lbl = QLabel()
        self._result_lbl.setWordWrap(True)
        self._result_lbl.setTextFormat(Qt.PlainText)
        self._result_lbl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._result_lbl.setStyleSheet(
            "color:#F0EDE8;font-size:13px;background:transparent;"
            "padding:10px;line-height:1.5;"
        )
        self._result_scroll.setWidget(self._result_lbl)
        exp_lay.addWidget(self._result_scroll)

        # Follow-up question row
        self._followup_row = QWidget()
        self._followup_row.setStyleSheet("background:transparent;")
        self._followup_row.hide()
        fu_lay = QHBoxLayout(self._followup_row)
        fu_lay.setContentsMargins(0, 0, 0, 0)
        fu_lay.setSpacing(6)

        self._question_input = QLineEdit()
        self._question_input.setPlaceholderText("Ask a follow-up question…")
        self._question_input.setStyleSheet(
            "QLineEdit{background:#343834;border:1px solid #3D413D;"
            "border-radius:8px;color:#F0EDE8;font-size:13px;padding:6px 10px;}"
            "QLineEdit:focus{border-color:#D4A017;}"
        )

        self._btn_send = QPushButton("→")
        self._btn_send.setFixedSize(32, 32)
        self._btn_send.setCursor(Qt.PointingHandCursor)
        self._btn_send.setStyleSheet(
            "QPushButton{background:#F0C94C;border-radius:8px;"
            "color:#1A1C1A;font-size:16px;font-weight:700;border:none;}"
            "QPushButton:hover{background:#E8B93A;}"
        )

        fu_lay.addWidget(self._question_input, 1)
        fu_lay.addWidget(self._btn_send)
        exp_lay.addWidget(self._followup_row)

        self._root.addWidget(self._action_bar)
        self._root.addWidget(self._expanded)

        # ── Wire ───────────────────────────────────────────────────────────────
        self._btn_explain.clicked.connect(self._on_explain)
        self._btn_ask.clicked.connect(self._on_ask)
        self._btn_close_idle.clicked.connect(self.hide)
        self._btn_close_exp.clicked.connect(self.hide)
        self._btn_send.clicked.connect(self._on_send_question)
        self._question_input.returnPressed.connect(self._on_send_question)

        # Spinner animation
        self._spinner_frames = ["⟳", "↻", "↺", "⟳"]
        self._spinner_idx    = 0
        self._spinner_timer  = QTimer(self)
        self._spinner_timer.timeout.connect(self._tick_spinner)

        self.hide()

    # ── Public API ─────────────────────────────────────────────────────────────

    def set_model(self, model: str):
        self._model = model

    def show_near(self, global_pos: QPoint, selected_text: str,
                  context: str = "", doc_name: str = ""):
        """Show the popup near the given GLOBAL screen position."""
        self._selected_text = selected_text
        self._context       = context
        self._doc_name      = doc_name

        self._show_idle()
        self.adjustSize()

        # Convert global position → local coordinates of our parent widget
        if self.parent():
            local_pos = self.parent().mapFromGlobal(global_pos)
        else:
            local_pos = global_pos

        x = local_pos.x() - self.width() // 2
        y = local_pos.y() - self.height() - 12

        # Keep inside parent bounds
        if self.parent():
            pw = self.parent().width()
            ph = self.parent().height()
            x = max(4, min(x, pw - self.width() - 4))
            if y < 4:
                y = local_pos.y() + 20   # show below if not enough room above

        self.move(x, y)
        self.show()
        self.raise_()

    # ── State helpers ──────────────────────────────────────────────────────────

    def _show_idle(self):
        self._action_bar.show()
        self._expanded.hide()
        self._result_scroll.hide()
        self._followup_row.hide()
        self._spinner_timer.stop()
        self.adjustSize()

    def _show_loading(self):
        self._action_bar.hide()
        self._expanded.show()
        self._status_lbl.show()
        self._status_lbl.setText("⟳  Generating…")
        self._result_scroll.hide()
        self._followup_row.hide()
        self._spinner_timer.start(300)
        self.adjustSize()

    def _show_result(self, text: str):
        self._spinner_timer.stop()
        self._status_lbl.hide()
        self._result_lbl.setText(text)
        self._result_scroll.show()
        self._followup_row.show()
        self.adjustSize()

    def _show_error(self, msg: str):
        self._spinner_timer.stop()
        self._status_lbl.setText(f"⚠  {msg}")
        self._status_lbl.setStyleSheet(
            "color:#E05555;font-size:13px;background:transparent;"
        )
        self._result_scroll.hide()
        self._followup_row.hide()
        self.adjustSize()

    def _tick_spinner(self):
        self._spinner_idx = (self._spinner_idx + 1) % len(self._spinner_frames)
        self._status_lbl.setText(
            f"{self._spinner_frames[self._spinner_idx]}  Generating…"
        )

    # ── Actions ────────────────────────────────────────────────────────────────

    def _on_explain(self):
        if not self._model:
            self._show_loading()
            self._show_error("No AI model selected.\nGo to Settings to choose one.")
            return
        prompt = context_service.build_explain_prompt(
            self._selected_text, self._context, self._doc_name
        )
        self._run_worker(prompt)

    def _on_ask(self):
        """Switch directly to the follow-up question mode."""
        self._action_bar.hide()
        self._expanded.show()
        self._status_lbl.hide()
        self._result_scroll.hide()
        self._followup_row.show()
        self._question_input.setFocus()
        self.adjustSize()

    def _on_send_question(self):
        question = self._question_input.text().strip()
        if not question:
            return
        if not self._model:
            self._show_error("No AI model selected.")
            return
        prompt = context_service.build_question_prompt(
            self._selected_text, self._context, question
        )
        self._question_input.clear()
        self._run_worker(prompt)

    def _run_worker(self, prompt: str):
        self._show_loading()
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
        self._worker = AIWorker(self._model, prompt, parent=self)
        self._worker.resultReady.connect(self._show_result)
        self._worker.errorOccurred.connect(self._show_error)
        self._worker.start()

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _action_btn(self, text: str) -> QPushButton:
        b = QPushButton(text)
        b.setCursor(Qt.PointingHandCursor)
        b.setStyleSheet(
            "QPushButton{background:transparent;color:#F0EDE8;"
            "font-size:13px;font-weight:500;padding:8px 14px;"
            "border:none;border-radius:8px;}"
            "QPushButton:hover{background:#343834;}"
        )
        return b
