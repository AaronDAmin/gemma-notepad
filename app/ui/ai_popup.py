"""AI contextual popup — explains selected text using a local Ollama model."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFrame, QScrollArea, QLineEdit, QGraphicsDropShadowEffect,
    QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QPoint, QTimer, QRectF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen

from app.services.context_service import context_service
from app.workers.ai_worker import AIWorker
from app.ui.icons import load_svg_pixmap


class AIContextPopup(QWidget):
    """
    Floating popup shown above selected text.
    Has a downward-pointing anchor beak towards the selected text.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.ClickFocus)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 75))
        self.setGraphicsEffect(shadow)

        self._model: str = ""
        self._selected_text: str = ""
        self._context: str = ""
        self._doc_name: str = ""
        self._worker: AIWorker | None = None
        self._beak_height = 7

        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(4, 4, 4, 4 + self._beak_height)
        self._root.setSpacing(0)

        # ── Action bar (idle state) ────────────────────────────────────────────
        self._action_bar = QWidget()
        self._action_bar.setStyleSheet("background: transparent;")
        ab_lay = QHBoxLayout(self._action_bar)
        ab_lay.setContentsMargins(6, 0, 6, 0)
        ab_lay.setSpacing(4)
        ab_lay.setAlignment(Qt.AlignVCenter)

        self._btn_explain = QPushButton(" Explain with AI")
        self._btn_explain.setCursor(Qt.PointingHandCursor)
        pix_sparkle = load_svg_pixmap("sparkle.svg", 14)
        self._btn_explain.setIcon(pix_sparkle)
        self._btn_explain.setIconSize(pix_sparkle.size())
        self._btn_explain.setStyleSheet(
            "QPushButton{"
            "background: transparent; color: #F0EDE8; font-size: 11.5px; font-weight: 600;"
            "padding: 4px 6px; border: none; border-radius: 5px;"
            "}"
            "QPushButton:hover{background-color: rgba(255, 255, 255, 0.10);}"
        )

        self._btn_ask = QPushButton(" Ask a question")
        self._btn_ask.setCursor(Qt.PointingHandCursor)
        pix_chat = load_svg_pixmap("chat_bubble.svg", 13)
        self._btn_ask.setIcon(pix_chat)
        self._btn_ask.setIconSize(pix_chat.size())
        self._btn_ask.setStyleSheet(
            "QPushButton{"
            "background: transparent; color: #F0EDE8; font-size: 11.5px; font-weight: 500;"
            "padding: 4px 6px; border: none; border-radius: 5px;"
            "}"
            "QPushButton:hover{background-color: rgba(255, 255, 255, 0.10);}"
        )

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedWidth(1)
        sep.setFixedHeight(16)
        sep.setStyleSheet("background: #3D413D;")

        self._btn_more = QPushButton("⋮")
        self._btn_more.setFixedSize(22, 22)
        self._btn_more.setCursor(Qt.PointingHandCursor)
        self._btn_more.setStyleSheet(
            "QPushButton{background: transparent; color: #8A9A8A; font-size: 15px; border: none; border-radius: 4px;}"
            "QPushButton:hover{background-color: rgba(255, 255, 255, 0.10); color: #F0EDE8;}"
        )

        ab_lay.addWidget(self._btn_explain)
        ab_lay.addWidget(self._btn_ask)
        ab_lay.addWidget(sep)
        ab_lay.addWidget(self._btn_more)

        # ── Expanded panel (loading / result / error) ──────────────────────────
        self._expanded = QWidget()
        self._expanded.setStyleSheet("background: transparent; border: none;")
        self._expanded.hide()
        exp_lay = QVBoxLayout(self._expanded)
        exp_lay.setContentsMargins(10, 8, 10, 8)
        exp_lay.setSpacing(6)

        close_row = QHBoxLayout()
        close_row.addStretch()
        self._btn_close_exp = QPushButton("✕")
        self._btn_close_exp.setFixedSize(20, 20)
        self._btn_close_exp.setCursor(Qt.PointingHandCursor)
        self._btn_close_exp.setStyleSheet(
            "QPushButton{background: transparent; color: #8A9A8A; font-size: 11px; border: none; border-radius: 4px;}"
            "QPushButton:hover{background: #343834; color: #F0EDE8;}"
        )
        close_row.addWidget(self._btn_close_exp)
        exp_lay.addLayout(close_row)

        self._status_lbl = QLabel("⟳  Generating…")
        self._status_lbl.setStyleSheet(
            "color: #D4A017; font-size: 12.5px; background: transparent; font-weight: 600;"
        )
        self._status_lbl.setAlignment(Qt.AlignCenter)
        exp_lay.addWidget(self._status_lbl)

        self._result_scroll = QScrollArea()
        self._result_scroll.setWidgetResizable(True)
        self._result_scroll.setFixedHeight(160)
        self._result_scroll.setFrameShape(QFrame.NoFrame)
        self._result_scroll.setStyleSheet(
            "QScrollArea{background: #181C19; border-radius: 8px; border: none;}"
            "QScrollArea > QWidget{background: #181C19;}"
        )
        self._result_scroll.hide()

        self._result_lbl = QLabel()
        self._result_lbl.setWordWrap(True)
        self._result_lbl.setTextFormat(Qt.PlainText)
        self._result_lbl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._result_lbl.setStyleSheet(
            "color: #F0EDE8; font-size: 12px; background: transparent; padding: 8px; line-height: 1.45;"
        )
        self._result_scroll.setWidget(self._result_lbl)
        exp_lay.addWidget(self._result_scroll)

        self._followup_row = QWidget()
        self._followup_row.setStyleSheet("background: transparent;")
        self._followup_row.hide()
        fu_lay = QHBoxLayout(self._followup_row)
        fu_lay.setContentsMargins(0, 0, 0, 0)
        fu_lay.setSpacing(6)

        self._question_input = QLineEdit()
        self._question_input.setPlaceholderText("Ask a follow-up question…")
        self._question_input.setStyleSheet(
            "QLineEdit{background: #343834; border: 1px solid #3D413D; border-radius: 6px; color: #F0EDE8; font-size: 12px; padding: 4px 8px;}"
            "QLineEdit:focus{border-color: #D4A017;}"
        )

        self._btn_send = QPushButton("→")
        self._btn_send.setFixedSize(26, 26)
        self._btn_send.setCursor(Qt.PointingHandCursor)
        self._btn_send.setStyleSheet(
            "QPushButton{background: #FFD04D; border-radius: 6px; color: #1A1C1A; font-size: 13px; font-weight: 700; border: none;}"
            "QPushButton:hover{background: #E8B93A;}"
        )

        fu_lay.addWidget(self._question_input, 1)
        fu_lay.addWidget(self._btn_send)
        exp_lay.addWidget(self._followup_row)

        self._root.addWidget(self._action_bar)
        self._root.addWidget(self._expanded)

        self._btn_explain.clicked.connect(self._on_explain)
        self._btn_ask.clicked.connect(self._on_ask)
        self._btn_more.clicked.connect(self._on_more)
        self._btn_close_exp.clicked.connect(self.hide)
        self._btn_send.clicked.connect(self._on_send_question)
        self._question_input.returnPressed.connect(self._on_send_question)

        self._spinner_frames = ["⟳", "↻", "↺", "⟳"]
        self._spinner_idx = 0
        self._spinner_timer = QTimer(self)
        self._spinner_timer.timeout.connect(self._tick_spinner)

        self._show_idle()
        self.hide()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        bh = self._beak_height
        rect_h = h - bh

        path = QPainterPath()
        path.addRoundedRect(0, 0, w, rect_h, 12, 12)

        cx = w / 2
        path.moveTo(cx - 6, rect_h)
        path.lineTo(cx, h - 0.5)
        path.lineTo(cx + 6, rect_h)
        path.closeSubpath()

        p.fillPath(path, QColor("#222825"))
        p.setPen(QPen(QColor("#38403C"), 1))
        p.drawPath(path)
        p.end()

    def set_model(self, model: str):
        self._model = model

    def show_near(self, global_pos: QPoint, selected_text: str,
                  context: str = "", doc_name: str = ""):
        self._selected_text = selected_text
        self._context       = context
        self._doc_name      = doc_name

        self._show_idle()

        if self.parent():
            local_pos = self.parent().mapFromGlobal(global_pos)
        else:
            local_pos = global_pos

        x = local_pos.x() - self.width() // 2
        y = local_pos.y() - self.height()

        if self.parent():
            pw = self.parent().width()
            x = max(10, min(x, pw - self.width() - 10))
            if y < 10:
                y = local_pos.y() + 24

        self.move(int(x), int(y))
        self.show()
        self.raise_()

    def _show_idle(self):
        self._action_bar.show()
        self._expanded.hide()
        self._result_scroll.hide()
        self._followup_row.hide()
        self._spinner_timer.stop()
        self.setFixedSize(276, 42)
        self.update()

    def _show_loading(self):
        self._action_bar.hide()
        self._expanded.show()
        self._status_lbl.show()
        self._status_lbl.setText("⟳  Generating…")
        self._result_scroll.hide()
        self._followup_row.hide()
        self._spinner_timer.start(300)
        self.setFixedSize(330, 110)
        self.update()

    def _show_result(self, text: str):
        self._spinner_timer.stop()
        self._status_lbl.hide()
        self._result_lbl.setText(text)
        self._result_scroll.show()
        self._followup_row.show()
        self.setFixedSize(330, 250)
        self.update()

    def _show_error(self, msg: str):
        self._spinner_timer.stop()
        self._status_lbl.setText(f"⚠  {msg}")
        self._status_lbl.setStyleSheet(
            "color: #E05555; font-size: 12px; background: transparent;"
        )
        self._result_scroll.hide()
        self._followup_row.hide()
        self.setFixedSize(330, 100)
        self.update()

    def _tick_spinner(self):
        self._spinner_idx = (self._spinner_idx + 1) % len(self._spinner_frames)
        self._status_lbl.setText(
            f"{self._spinner_frames[self._spinner_idx]}  Generating…"
        )

    def _on_explain(self):
        if not self._model:
            self._show_loading()
            self._show_error("No AI model configured.\nSelect a model in Settings.")
            return
        prompt = context_service.build_explain_prompt(
            self._selected_text, self._context, self._doc_name
        )
        self._run_worker(prompt)

    def _on_ask(self):
        self._action_bar.hide()
        self._expanded.show()
        self._status_lbl.hide()
        self._result_scroll.hide()
        self._followup_row.show()
        self._question_input.setFocus()
        self.setFixedSize(330, 90)
        self.update()

    def _on_more(self):
        self._on_ask()

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
