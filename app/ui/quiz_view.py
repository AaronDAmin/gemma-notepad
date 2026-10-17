"""Quiz interface — config → generation → questions → results."""
from __future__ import annotations
import pymupdf as fitz
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QComboBox, QSpinBox, QButtonGroup, QProgressBar, QScrollArea,
    QStackedWidget, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from app.workers.quiz_worker import QuizWorker
from app.services.pdf_service import pdf_service


# ── Shared styles ──────────────────────────────────────────────────────────────
_COMBO_SS = (
    "QComboBox{background:#FFF8EC;border:1px solid #EDD89A;"
    "border-radius:8px;color:#1A1C1A;padding:5px 10px;font-size:13px;}"
    "QComboBox::drop-down{border:none;width:20px;}"
    "QComboBox QAbstractItemView{background:#FFF8EC;color:#1A1C1A;"
    "selection-background-color:#F0C94C;}"
)
_SPIN_SS = (
    "QSpinBox{background:#FFF8EC;border:1px solid #EDD89A;"
    "border-radius:8px;color:#1A1C1A;padding:5px 10px;font-size:13px;}"
)
_BTN_PRIMARY = (
    "QPushButton{background:#F0C94C;border-radius:10px;color:#1A1C1A;"
    "font-size:13px;font-weight:600;padding:8px 24px;border:none;}"
    "QPushButton:hover{background:#E8B93A;}"
    "QPushButton:pressed{background:#D4A017;}"
)
_BTN_SECONDARY = (
    "QPushButton{background:#F7E7B5;border-radius:10px;color:#1A1C1A;"
    "font-size:13px;font-weight:500;padding:8px 20px;border:none;}"
    "QPushButton:hover{background:#EDD89A;}"
)
_CHOICE_SS = (
    "QPushButton{background:#F7E7B5;border-radius:10px;color:#1A1C1A;"
    "font-size:13px;font-weight:500;padding:12px 16px;text-align:left;"
    "border:2px solid transparent;}"
    "QPushButton:hover{background:#EDD89A;}"
    "QPushButton:checked{background:#FBF0CC;"
    "border:2px solid #F0C94C;font-weight:600;}"
)


def _card_widget() -> QFrame:
    f = QFrame()
    f.setStyleSheet("QFrame{background:#F7E7B5;border-radius:12px;}")
    return f


def _label(text: str, color: str = "#1A1C1A", size: int = 13,
           bold: bool = False, wrap: bool = False) -> QLabel:
    l = QLabel(text)
    l.setWordWrap(wrap)
    l.setStyleSheet(
        f"color:{color};font-size:{size}px;"
        f"font-weight:{'700' if bold else '400'};"
        "background:transparent;"
    )
    return l


# ── 0. Config form ─────────────────────────────────────────────────────────────

class QuizConfigForm(QWidget):
    generateRequested = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QWidget{background:#FFF8EC;border-radius:16px;}")

        self._total_pages  = 0
        self._current_page = 1

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(14)

        root.addWidget(_label("Generate a Quiz", "#D4A017", 22, bold=True))
        root.addWidget(_label("Configure the quiz below, then click Generate.", "#4A4E4A"))
        root.addSpacing(4)

        card = _card_widget()
        lay  = QVBoxLayout(card)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(10)

        def field(lbl_text, widget):
            row = QHBoxLayout()
            l = QLabel(lbl_text)
            l.setFixedWidth(160)
            l.setStyleSheet("color:#4A4E4A;font-size:13px;background:transparent;")
            row.addWidget(l)
            row.addWidget(widget, 1)
            lay.addLayout(row)

        # ── Scope selector ─────────────────────────────────────────────────────
        self.scope_combo = QComboBox()
        self.scope_combo.addItem("Current page only", "current")
        self.scope_combo.addItem("Page range", "range")
        self.scope_combo.setStyleSheet(_COMBO_SS)
        self.scope_combo.currentIndexChanged.connect(self._on_scope_changed)
        field("Source", self.scope_combo)

        # ── Page range row (hidden by default) ────────────────────────────────
        self._range_row = QWidget()
        self._range_row.setStyleSheet("background:transparent;")
        range_lay = QHBoxLayout(self._range_row)
        range_lay.setContentsMargins(0, 0, 0, 0)
        range_lay.setSpacing(8)

        range_lbl = QLabel("Pages")
        range_lbl.setFixedWidth(160)
        range_lbl.setStyleSheet("color:#4A4E4A;font-size:13px;background:transparent;")

        self.page_from = QSpinBox()
        self.page_from.setRange(1, 20)
        self.page_from.setValue(1)
        self.page_from.setStyleSheet(_SPIN_SS)
        self.page_from.setFixedWidth(70)

        sep_lbl = QLabel("to")
        sep_lbl.setStyleSheet("color:#4A4E4A;font-size:13px;background:transparent;")

        self.page_to = QSpinBox()
        self.page_to.setRange(1, 20)
        self.page_to.setValue(1)
        self.page_to.setStyleSheet(_SPIN_SS)
        self.page_to.setFixedWidth(70)

        range_lay.addWidget(range_lbl)
        range_lay.addWidget(self.page_from)
        range_lay.addWidget(sep_lbl)
        range_lay.addWidget(self.page_to)
        range_lay.addStretch()
        self._range_row.hide()
        lay.addWidget(self._range_row)

        # ── Other fields ───────────────────────────────────────────────────────
        self.num_spin = QSpinBox()
        self.num_spin.setRange(1, 10)
        self.num_spin.setValue(3)
        self.num_spin.setStyleSheet(_SPIN_SS)

        self.diff_combo = QComboBox()
        self.diff_combo.addItems(["Easy", "Medium", "Hard"])
        self.diff_combo.setCurrentText("Medium")
        self.diff_combo.setStyleSheet(_COMBO_SS)

        self.focus_combo = QComboBox()
        self.focus_combo.addItems(["Memorization", "Understanding", "Application"])
        self.focus_combo.setCurrentText("Understanding")
        self.focus_combo.setStyleSheet(_COMBO_SS)

        field("Number of questions", self.num_spin)
        field("Difficulty", self.diff_combo)
        field("Focus", self.focus_combo)

        root.addWidget(card)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.gen_btn = QPushButton("✦  Generate Quiz")
        self.gen_btn.setCursor(Qt.PointingHandCursor)
        self.gen_btn.setStyleSheet(_BTN_PRIMARY)
        self.gen_btn.clicked.connect(self._emit)
        btn_row.addWidget(self.gen_btn)
        root.addLayout(btn_row)
        root.addStretch()

    def update_page_info(self, current_page: int, total_pages: int):
        """Called by QuizView when context changes."""
        self._current_page = current_page
        self._total_pages  = total_pages
        max_p = max(total_pages, 1)
        self.page_from.setRange(1, max_p)
        self.page_to.setRange(1, max_p)
        self.page_from.setValue(current_page)
        self.page_to.setValue(current_page)

    def _on_scope_changed(self, idx: int):
        self._range_row.setVisible(self.scope_combo.currentData() == "range")

    def _emit(self):
        scope = self.scope_combo.currentData()
        if scope == "current":
            page_range = (self._current_page, self._current_page)
        else:
            p_from = self.page_from.value()
            p_to   = max(self.page_to.value(), p_from)
            page_range = (p_from, p_to)

        self.generateRequested.emit({
            "num_questions": self.num_spin.value(),
            "difficulty":    self.diff_combo.currentText().lower(),
            "focus":         self.focus_combo.currentText().lower(),
            "page_range":    page_range,
        })


# ── 1. Loading screen ──────────────────────────────────────────────────────────

class QuizLoadingScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QWidget{background:#FFF8EC;border-radius:16px;}")
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(16)

        self._spinner = QLabel("⟳")
        self._spinner.setAlignment(Qt.AlignCenter)
        self._spinner.setStyleSheet(
            "color:#D4A017;font-size:40px;background:transparent;"
        )

        self._msg = _label("Generating quiz… this may take 1–3 minutes.", "#4A4E4A", 14)
        self._msg.setAlignment(Qt.AlignCenter)
        self._msg.setWordWrap(True)

        lay.addWidget(self._spinner)
        lay.addWidget(self._msg)

        from PySide6.QtCore import QTimer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._frames = ["⟳", "↻", "↺"]
        self._idx = 0

    def start(self):
        self._timer.start(250)

    def stop(self):
        self._timer.stop()

    def _tick(self):
        self._idx = (self._idx + 1) % len(self._frames)
        self._spinner.setText(self._frames[self._idx])


# ── 2. Question view ───────────────────────────────────────────────────────────

class QuizQuestionView(QWidget):
    submitRequested = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QWidget{background:#FFF8EC;border-radius:16px;}")

        self._questions : list[dict] = []
        self._current   : int        = 0
        self._answers   : dict       = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(12)

        hdr = QHBoxLayout()
        self.progress_lbl = _label("Question 1 of 5", "#4A4E4A", 13, bold=True)
        hdr.addStretch()
        hdr.addWidget(self.progress_lbl)
        root.addLayout(hdr)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet(
            "QProgressBar{background:#EDD89A;border-radius:3px;}"
            "QProgressBar::chunk{background:#F0C94C;border-radius:3px;}"
        )
        root.addWidget(self.progress_bar)

        self.q_label = QLabel()
        self.q_label.setWordWrap(True)
        self.q_label.setStyleSheet(
            "color:#1A1C1A;font-size:15px;font-weight:600;background:transparent;"
        )
        root.addWidget(self.q_label)
        root.addSpacing(4)

        self._btn_group = QButtonGroup(self)
        self._btn_group.setExclusive(True)
        self._choice_btns: list[QPushButton] = []
        for key in ("A", "B", "C", "D"):
            btn = QPushButton()
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(48)
            btn.setStyleSheet(_CHOICE_SS)
            btn.setProperty("option_key", key)
            self._btn_group.addButton(btn)
            self._choice_btns.append(btn)
            root.addWidget(btn)

        root.addStretch()

        nav = QHBoxLayout()
        self.prev_btn = QPushButton("‹  Previous")
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.prev_btn.setStyleSheet(_BTN_SECONDARY)
        self.prev_btn.clicked.connect(self._prev)

        self.next_btn = QPushButton("Next  ›")
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.setStyleSheet(_BTN_PRIMARY)
        self.next_btn.clicked.connect(self._next)

        self.submit_btn = QPushButton("✔  Submit Quiz")
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.submit_btn.setStyleSheet(_BTN_PRIMARY)
        self.submit_btn.clicked.connect(self._submit)
        self.submit_btn.hide()

        nav.addWidget(self.prev_btn)
        nav.addStretch()
        nav.addWidget(self.next_btn)
        nav.addWidget(self.submit_btn)
        root.addLayout(nav)

    def load_questions(self, questions: list[dict]):
        self._questions = questions
        self._current   = 0
        self._answers   = {}
        self.progress_bar.setRange(0, len(questions))
        self._render()

    def _render(self):
        n   = len(self._questions)
        idx = self._current
        q   = self._questions[idx]

        self.progress_lbl.setText(f"Question {idx + 1} of {n}")
        self.progress_bar.setValue(idx + 1)
        self.q_label.setText(q["question"])

        self._btn_group.blockSignals(True)
        for btn in self._choice_btns:
            key  = btn.property("option_key")
            text = q["options"].get(key, "")
            btn.setText(f"  {key}.  {text}")
            btn.setChecked(self._answers.get(idx) == key)
        self._btn_group.blockSignals(False)

        self.prev_btn.setEnabled(idx > 0)
        self.next_btn.setVisible(idx < n - 1)
        self.submit_btn.setVisible(idx == n - 1)

    def _save_answer(self):
        for btn in self._choice_btns:
            if btn.isChecked():
                self._answers[self._current] = btn.property("option_key")
                return

    def _prev(self):
        self._save_answer()
        if self._current > 0:
            self._current -= 1
            self._render()

    def _next(self):
        self._save_answer()
        if self._current < len(self._questions) - 1:
            self._current += 1
            self._render()

    def _submit(self):
        self._save_answer()
        self.submitRequested.emit(self._answers)


# ── 3. Results screen ──────────────────────────────────────────────────────────

class QuizResultsView(QWidget):
    retryRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QWidget{background:#FFF8EC;border-radius:16px;}")

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(14)

        self.score_lbl = _label("", "#D4A017", 26, bold=True)
        self.score_lbl.setAlignment(Qt.AlignCenter)
        root.addWidget(self.score_lbl)

        self.subtitle_lbl = _label("", "#4A4E4A", 14)
        self.subtitle_lbl.setAlignment(Qt.AlignCenter)
        root.addWidget(self.subtitle_lbl)
        root.addSpacing(8)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea{background:transparent;border:none;}"
            "QScrollArea > QWidget{background:transparent;}"
        )
        self._detail_widget = QWidget()
        self._detail_widget.setStyleSheet("background:transparent;")
        self._detail_layout = QVBoxLayout(self._detail_widget)
        self._detail_layout.setSpacing(10)
        scroll.setWidget(self._detail_widget)
        root.addWidget(scroll, 1)

        retry_row = QHBoxLayout()
        retry_row.addStretch()
        self.retry_btn = QPushButton("↺  New Quiz")
        self.retry_btn.setCursor(Qt.PointingHandCursor)
        self.retry_btn.setStyleSheet(_BTN_PRIMARY)
        self.retry_btn.clicked.connect(self.retryRequested)
        retry_row.addWidget(self.retry_btn)
        root.addLayout(retry_row)

    def show_results(self, questions: list[dict], answers: dict):
        while self._detail_layout.count():
            item = self._detail_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        correct = sum(
            1 for i, q in enumerate(questions)
            if answers.get(i, "") == q["correct"]
        )
        total = len(questions)
        pct   = int(correct / total * 100) if total else 0

        self.score_lbl.setText(f"{correct} / {total}  ({pct}%)")
        emoji = "🎉" if pct >= 70 else "📚"
        self.subtitle_lbl.setText(
            f"{emoji}  {'Great job!' if pct >= 70 else 'Keep studying!'}"
        )

        for i, q in enumerate(questions):
            chosen      = answers.get(i, "—")
            correct_opt = q["correct"]
            is_ok       = chosen == correct_opt

            card = _card_widget()
            card.setStyleSheet(
                f"QFrame{{background:{'#E8F5E8' if is_ok else '#FDE8E8'};"
                "border-radius:10px;}}"
            )
            lay = QVBoxLayout(card)
            lay.setContentsMargins(14, 10, 14, 10)
            lay.setSpacing(4)

            lay.addWidget(_label(f"Q{i+1}. {q['question']}", "#1A1C1A", 13, bold=True, wrap=True))

            chosen_text = q["options"].get(chosen, "No answer")
            status = "✓" if is_ok else "✗"
            color  = "#2E7D32" if is_ok else "#C62828"
            lay.addWidget(_label(
                f"{status}  Your answer: {chosen}. {chosen_text}",
                color, 13, wrap=True
            ))

            if not is_ok:
                correct_text = q["options"].get(correct_opt, "")
                lay.addWidget(_label(
                    f"✓  Correct: {correct_opt}. {correct_text}",
                    "#2E7D32", 13, wrap=True
                ))

            lay.addWidget(_label(
                f"💡 {q.get('explanation', '')}",
                "#4A4E4A", 12, wrap=True
            ))

            self._detail_layout.addWidget(card)

        self._detail_layout.addStretch()


# ── Main QuizView container ────────────────────────────────────────────────────

class QuizView(QWidget):
    """Stacks: 0=config, 1=loading, 2=questions, 3=results."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self._model        : str              = ""
        self._doc                             = None   # fitz.Document or None
        self._doc_name     : str              = ""
        self._total_pages  : int              = 0
        self._current_page : int              = 1
        self._questions    : list[dict]       = []
        self._worker       : QuizWorker | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._stack = QStackedWidget()

        self.config_form    = QuizConfigForm()
        self.loading_screen = QuizLoadingScreen()
        self.question_view  = QuizQuestionView()
        self.results_view   = QuizResultsView()

        self._stack.addWidget(self.config_form)     # 0
        self._stack.addWidget(self.loading_screen)  # 1
        self._stack.addWidget(self.question_view)   # 2
        self._stack.addWidget(self.results_view)    # 3

        root.addWidget(self._stack)

        self.config_form.generateRequested.connect(self._on_generate)
        self.question_view.submitRequested.connect(self._on_submit)
        self.results_view.retryRequested.connect(self._on_retry)

    # ── Public API ─────────────────────────────────────────────────────────────

    def set_context(self, model: str, doc=None, doc_name: str = "",
                    total_pages: int = 0, current_page: int = 1):
        self._model        = model
        self._doc          = doc
        self._doc_name     = doc_name
        self._total_pages  = total_pages
        self._current_page = current_page
        self.config_form.update_page_info(current_page, total_pages)

    def reset(self):
        self._stack.setCurrentIndex(0)

    # ── Internal ───────────────────────────────────────────────────────────────

    def _on_generate(self, config: dict):
        if not self._model:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "No model",
                "Please select an AI model in Settings first.")
            return
        if self._doc is None:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "No document",
                "Please open a PDF document before generating a quiz.")
            return

        # Extract text from selected page range (1-based)
        p_from, p_to = config["page_range"]
        p_from = max(1, p_from)
        p_to   = min(p_to, self._doc.page_count)

        page_texts = []
        for p in range(p_from - 1, p_to):   # 0-based for PyMuPDF
            blocks = pdf_service.get_text_blocks(self._doc, p)
            page_texts.append("\n".join(b["text"] for b in blocks))
        doc_text = "\n\n".join(page_texts).strip()

        if not doc_text:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "No text",
                "No text found on the selected pages.\n"
                "Try a different page range.")
            return

        n = config["num_questions"]
        if n > 3:
            from PySide6.QtWidgets import QMessageBox
            ret = QMessageBox.question(
                self, "Generation time",
                f"Generating {n} questions may take 1–3 minutes.\nContinue?",
                QMessageBox.Yes | QMessageBox.No
            )
            if ret != QMessageBox.Yes:
                return

        self._stack.setCurrentIndex(1)
        self.loading_screen.start()

        self._worker = QuizWorker(
            self._model, doc_text,
            config["num_questions"],
            config["difficulty"],
            config["focus"],
            parent=self
        )
        self._worker.resultReady.connect(self._on_questions_ready)
        self._worker.errorOccurred.connect(self._on_error)
        self._worker.start()

    def _on_questions_ready(self, questions: list[dict]):
        self.loading_screen.stop()
        self._questions = questions
        self.question_view.load_questions(questions)
        self._stack.setCurrentIndex(2)

    def _on_error(self, msg: str):
        self.loading_screen.stop()
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(self, "Quiz generation failed", msg)
        self._stack.setCurrentIndex(0)

    def _on_submit(self, answers: dict):
        self.results_view.show_results(self._questions, answers)
        self._stack.setCurrentIndex(3)

    def _on_retry(self):
        self._stack.setCurrentIndex(0)
