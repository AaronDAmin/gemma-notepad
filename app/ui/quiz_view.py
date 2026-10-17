"""Quiz interface widget — configuration form and placeholder MCQ view.
Phase 1: UI shell.
Phase 4 will wire in the quiz engine.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QComboBox, QSpinBox, QButtonGroup,
    QSizePolicy, QProgressBar
)
from PySide6.QtCore import Qt, Signal


# ── Reusable small widgets ─────────────────────────────────────────────────────

class SectionCard(QFrame):
    """A cream-tinted card container for grouping form elements."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            "QFrame{background:#F7E7B5; border-radius:12px;}"
        )
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(18, 14, 18, 14)
        self._layout.setSpacing(10)

    def inner_layout(self):
        return self._layout


class FieldRow(QHBoxLayout):
    """Label + widget side-by-side row."""

    def __init__(self, label_text: str, widget: QWidget):
        super().__init__()
        self.setSpacing(12)
        lbl = QLabel(label_text)
        lbl.setStyleSheet(
            "color:#4A4E4A; font-size:13px; background:transparent;"
        )
        lbl.setFixedWidth(160)
        self.addWidget(lbl)
        self.addWidget(widget, 1)


# ── Quiz configuration form ────────────────────────────────────────────────────

class QuizConfigForm(QWidget):
    """Form where the user configures quiz parameters before generation."""

    generateRequested = Signal(dict)   # emits config dict

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("quizContainer")
        self.setStyleSheet(
            "#quizContainer{background:#FFF8EC; border-radius:16px;}"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(16)

        # Header
        title = QLabel("Generate a Quiz")
        title.setObjectName("quizTitle")
        title.setStyleSheet(
            "color:#D4A017; font-size:22px; font-weight:700; background:transparent;"
        )
        subtitle = QLabel(
            "Customise the quiz parameters below, then click Generate."
        )
        subtitle.setStyleSheet(
            "color:#4A4E4A; font-size:13px; background:transparent;"
        )

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addSpacing(4)

        # ── Config card ────────────────────────────────────────────────────────
        card = SectionCard()
        inner = card.inner_layout()

        # Document selector
        self.doc_combo = QComboBox()
        self.doc_combo.setStyleSheet(
            "QComboBox{background:#FFF8EC;border:1px solid #EDD89A;"
            "border-radius:8px;color:#1A1C1A;padding:5px 10px;font-size:13px;}"
            "QComboBox::drop-down{border:none;width:20px;}"
            "QComboBox QAbstractItemView{background:#FFF8EC;color:#1A1C1A;"
            "selection-background-color:#F0C94C;}"
        )
        self.doc_combo.addItem("Current document")
        inner.addLayout(FieldRow("Document / Chapter", self.doc_combo))

        # Number of questions
        self.num_spin = QSpinBox()
        self.num_spin.setRange(1, 20)
        self.num_spin.setValue(5)
        self.num_spin.setStyleSheet(
            "QSpinBox{background:#FFF8EC;border:1px solid #EDD89A;"
            "border-radius:8px;color:#1A1C1A;padding:5px 10px;font-size:13px;}"
        )
        inner.addLayout(FieldRow("Number of questions", self.num_spin))

        # Difficulty
        self.diff_combo = QComboBox()
        self.diff_combo.addItems(["Easy", "Medium", "Hard"])
        self.diff_combo.setCurrentText("Medium")
        self.diff_combo.setStyleSheet(self.doc_combo.styleSheet())
        inner.addLayout(FieldRow("Difficulty", self.diff_combo))

        # Focus
        self.focus_combo = QComboBox()
        self.focus_combo.addItems(["Memorization", "Understanding", "Application"])
        self.focus_combo.setCurrentText("Understanding")
        self.focus_combo.setStyleSheet(self.doc_combo.styleSheet())
        inner.addLayout(FieldRow("Question focus", self.focus_combo))

        root.addWidget(card)

        # ── Generate button ────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.generate_btn = QPushButton("✦  Generate Quiz")
        self.generate_btn.setObjectName("primaryBtn")
        self.generate_btn.setCursor(Qt.PointingHandCursor)
        self.generate_btn.setStyleSheet(
            "QPushButton{background:#F0C94C;border-radius:10px;color:#1A1C1A;"
            "font-size:14px;font-weight:600;padding:10px 28px;min-height:42px;}"
            "QPushButton:hover{background:#E8B93A;}"
            "QPushButton:pressed{background:#D4A017;}"
        )
        self.generate_btn.clicked.connect(self._on_generate)
        btn_row.addWidget(self.generate_btn)
        root.addLayout(btn_row)

        root.addStretch()

    def _on_generate(self):
        config = {
            "document": self.doc_combo.currentText(),
            "num_questions": self.num_spin.value(),
            "difficulty": self.diff_combo.currentText().lower(),
            "focus": self.focus_combo.currentText().lower(),
        }
        self.generateRequested.emit(config)


# ── Quiz question view (placeholder) ──────────────────────────────────────────

class QuizQuestionView(QWidget):
    """Displays a single MCQ with A/B/C/D choices and navigation."""

    submitRequested = Signal()
    # backRequested removed — navigation handled by QuizView stack

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("quizContainer")
        self.setStyleSheet(
            "#quizContainer{background:#FFF8EC; border-radius:16px;}"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(14)

        # ── Header ─────────────────────────────────────────────────────────────
        header_row = QHBoxLayout()
        self.progress_lbl = QLabel("Question 1 of 5")
        self.progress_lbl.setStyleSheet(
            "color:#4A4E4A; font-size:13px; font-weight:600; background:transparent;"
        )
        header_row.addStretch()
        header_row.addWidget(self.progress_lbl)
        root.addLayout(header_row)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 5)
        self.progress_bar.setValue(1)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet(
            "QProgressBar{background:#EDD89A;border-radius:3px;}"
            "QProgressBar::chunk{background:#F0C94C;border-radius:3px;}"
        )
        root.addWidget(self.progress_bar)

        # ── Question text ──────────────────────────────────────────────────────
        self.q_label = QLabel(
            "What is the primary purpose of a Database Management System (DBMS)?"
        )
        self.q_label.setWordWrap(True)
        self.q_label.setStyleSheet(
            "color:#1A1C1A; font-size:16px; font-weight:600; background:transparent;"
        )
        root.addWidget(self.q_label)
        root.addSpacing(4)

        # ── Answer choices ─────────────────────────────────────────────────────
        choices = [
            ("A", "To provide a graphical user interface for databases"),
            ("B", "To allow users to define, create, maintain, and control access to a database"),
            ("C", "To replace spreadsheet software in organisations"),
            ("D", "To automatically back up data to cloud storage"),
        ]

        self._btn_group = QButtonGroup(self)
        self._answer_btns: list[QPushButton] = []

        for key, text in choices:
            btn = QPushButton(f"  {key}.  {text}")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(self._choice_style(False))
            btn.toggled.connect(lambda checked, b=btn: self._on_choice(b, checked))
            btn.setMinimumHeight(46)
            btn.setStyleSheet(self._choice_style_sheet())
            self._btn_group.addButton(btn)
            self._answer_btns.append(btn)
            root.addWidget(btn)

        root.addStretch()

        # ── Navigation ─────────────────────────────────────────────────────────
        nav_row = QHBoxLayout()

        self.prev_btn = QPushButton("‹  Previous")
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.prev_btn.setStyleSheet(
            "QPushButton{background:#F7E7B5;border-radius:10px;color:#1A1C1A;"
            "font-size:13px;font-weight:500;padding:8px 20px;}"
            "QPushButton:hover{background:#EDD89A;}"
        )

        self.next_btn = QPushButton("Next  ›")
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.setStyleSheet(
            "QPushButton{background:#F0C94C;border-radius:10px;color:#1A1C1A;"
            "font-size:13px;font-weight:600;padding:8px 20px;}"
            "QPushButton:hover{background:#E8B93A;}"
        )

        self.submit_btn = QPushButton("✔  Submit Quiz")
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.submit_btn.setStyleSheet(
            "QPushButton{background:#F0C94C;border-radius:10px;color:#1A1C1A;"
            "font-size:13px;font-weight:700;padding:8px 24px;}"
            "QPushButton:hover{background:#E8B93A;}"
        )
        self.submit_btn.clicked.connect(self.submitRequested)
        self.submit_btn.hide()   # shown on last question

        nav_row.addWidget(self.prev_btn)
        nav_row.addStretch()
        nav_row.addWidget(self.next_btn)
        nav_row.addWidget(self.submit_btn)
        root.addLayout(nav_row)

    def _choice_style(self, _: bool) -> str:
        return ""   # placeholder — real style applied via stylesheet below

    def _choice_style_sheet(self) -> str:
        return (
            "QPushButton{background:#F7E7B5;border-radius:10px;color:#1A1C1A;"
            "font-size:13px;font-weight:500;padding:10px 16px;text-align:left;"
            "border:2px solid transparent;}"
            "QPushButton:hover{background:#EDD89A;}"
            "QPushButton:checked{background:#FBF0CC;"
            "border:2px solid #F0C94C;font-weight:600;}"
        )

    def _on_choice(self, btn: QPushButton, checked: bool):
        pass   # Phase 4 will record the selection


# ── Main Quiz widget (stacks config + question views) ─────────────────────────

class QuizView(QWidget):
    """
    Outer container that switches between the config form and the question view.
    """

    returnToDocRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        from PySide6.QtWidgets import QStackedWidget
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._stack = QStackedWidget()

        self.config_form = QuizConfigForm()
        self.question_view = QuizQuestionView()

        self._stack.addWidget(self.config_form)    # index 0
        self._stack.addWidget(self.question_view)  # index 1

        root.addWidget(self._stack)

        # Connections
        self.config_form.generateRequested.connect(self._start_quiz)
        self.question_view.submitRequested.connect(self._on_submit)

    def _start_quiz(self, config: dict):
        """Switch to the question view (Phase 4 will actually generate questions)."""
        self._stack.setCurrentIndex(1)

    def _back_to_config(self):
        self._stack.setCurrentIndex(0)

    def _on_submit(self):
        """Phase 4 will show the results screen."""
        pass

    def reset(self):
        self._stack.setCurrentIndex(0)
