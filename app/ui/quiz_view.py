"""Quiz interface — faithful reproduction of reference mockups:
- NotepadLLM Quiz Configuration Dashboard.png
- AI Quiz Generation Dashboard.png
- Warm DBMS Quiz Dashboard.png
- NotepadLLM Quiz Results Dashboard.png
"""
from __future__ import annotations
import os
import pymupdf as fitz
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QComboBox, QSpinBox, QProgressBar, QScrollArea,
    QStackedWidget, QSizePolicy, QDialog
)
from PySide6.QtCore import Qt, Signal, QTimer, QTime
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont

from app.workers.quiz_worker import QuizWorker
from app.services.pdf_service import pdf_service
from app.ui.dialogs.ai_explanation_dialog import AIExplanationDialog
from app.ui.dialogs.ai_followup_dialog import AIFollowUpDialog


def _clear_layout(layout):
    """Recursively remove and delete all items and sublayouts."""
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            w = item.widget()
            w.setParent(None)
            w.deleteLater()
        elif item.layout():
            _clear_layout(item.layout())


# Sample authentic DBMS questions matching reference mockups
DEFAULT_DBMS_QUESTIONS = [
    {
        "question": "What is a DBMS?",
        "options": {
            "A": "A software system that allows users to define, create, maintain, and control access to a database.",
            "B": "A programming language used exclusively for web development.",
            "C": "A physical storage server located in a data center.",
            "D": "A networking protocol for transferring binary data packets."
        },
        "correct": "A",
        "explanation": "A DBMS (Database Management System) is software that provides an interface to manage data, including definition, creation, maintenance, and access control.",
        "page": 3
    },
    {
        "question": "Which component stores data physically?",
        "options": {
            "A": "Query Processor",
            "B": "Transaction Manager",
            "C": "Storage Manager",
            "D": "Authorization Manager"
        },
        "correct": "C",
        "explanation": "The Storage Manager is the component in a DBMS that is responsible for storing, retrieving, and managing data on disk. The Query Processor handles query parsing and optimization.",
        "page": 5
    },
    {
        "question": "Which of the following best describes a Database Management System (DBMS)?",
        "options": {
            "A": "A hardware device used to store data.",
            "B": "A software system used to define, create, maintain, and control access to a database.",
            "C": "A programming language for data analysis.",
            "D": "A network protocol used for data transfer."
        },
        "correct": "B",
        "explanation": "A DBMS is a set of software programs that controls the creation, maintenance, and use of a database.",
        "page": 5
    },
    {
        "question": "What does SQL stand for?",
        "options": {
            "A": "Structured Query Language",
            "B": "Simple Question Logic",
            "C": "System Query Language",
            "D": "Sequential Query Level"
        },
        "correct": "A",
        "explanation": "SQL (Structured Query Language) is a standard language used to define, manipulate, and query data in relational databases.",
        "page": 7
    },
    {
        "question": "Which of the following ensures data independence?",
        "options": {
            "A": "Direct Disk Access",
            "B": "Concurrency Control",
            "C": "Three-schema architecture",
            "D": "Network Topologies"
        },
        "correct": "C",
        "explanation": "The three-schema architecture (external, conceptual, internal schemas) provides data independence by separating user views from physical storage structures.",
        "page": 12
    },
    {
        "question": "What is data redundancy?",
        "options": {
            "A": "The duplication of data across multiple files or tables.",
            "B": "The corruption of data caused by hardware failure.",
            "C": "The encryption of data in transit.",
            "D": "The loss of historical logs during backup."
        },
        "correct": "A",
        "explanation": "Data redundancy occurs when the same piece of data is stored in multiple places within a database.",
        "page": 14
    },
    {
        "question": "Which type of DBMS is most common?",
        "options": {
            "A": "Relational DBMS (RDBMS)",
            "B": "Hierarchical DBMS",
            "C": "Network DBMS",
            "D": "Flat File DBMS"
        },
        "correct": "A",
        "explanation": "Relational Database Management Systems (RDBMS) based on tables and relations are the most widely used DBMS architecture.",
        "page": 16
    },
    {
        "question": "What does ACID stand for?",
        "options": {
            "A": "Atomicity, Consistency, Isolation, Durability",
            "B": "Access, Control, Identification, Data",
            "C": "Authentication, Concurrency, Integrity, Distribution",
            "D": "Allocation, Cache, Index, Directory"
        },
        "correct": "A",
        "explanation": "ACID properties guarantee that database transactions are processed reliably.",
        "page": 18
    },
    {
        "question": "What is a primary key?",
        "options": {
            "A": "A column or set of columns that uniquely identifies each row in a table.",
            "B": "The password used by the database administrator.",
            "C": "The main storage block index on the hard drive.",
            "D": "An encryption key used for SSL connections."
        },
        "correct": "A",
        "explanation": "A primary key uniquely identifies each record in a database table and cannot contain null values.",
        "page": 19
    },
    {
        "question": "Which layer interacts directly with end users and applications?",
        "options": {
            "A": "External / View Level",
            "B": "Internal / Physical Level",
            "C": "Storage Engine Level",
            "D": "Buffer Pool Level"
        },
        "correct": "A",
        "explanation": "The External or View level is the highest level of database abstraction, describing only the part of the database relevant to specific users.",
        "page": 20
    }
]


# ── Clickable Card Base Widget ─────────────────────────────────────────────────

class ClickableCard(QFrame):
    """Clickable container frame with hover and active states."""
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


# ── Radio Selection Card (e.g. Entire Document, Multiple Choice) ───────────────

class RadioSelectionCard(ClickableCard):
    def __init__(self, title: str, subtitle: str, is_active: bool = False, parent=None):
        super().__init__(parent)
        self.setFixedHeight(54)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 8, 14, 8)
        lay.setSpacing(10)

        self._radio_circle = QLabel("●" if is_active else "○")
        self._radio_circle.setStyleSheet(
            f"color: {'#FFD04D' if is_active else '#B0A898'}; font-size: 16px; background: transparent;"
        )

        t_col = QVBoxLayout()
        t_col.setSpacing(1)
        self._lbl_t = QLabel(title)
        self._lbl_t.setStyleSheet(
            f"color: #1A1C1A; font-size: 13px; font-weight: {'700' if is_active else '600'}; background: transparent;"
        )
        self._lbl_s = QLabel(subtitle)
        self._lbl_s.setStyleSheet("color: #7A7465; font-size: 11px; background: transparent;")
        t_col.addWidget(self._lbl_t)
        t_col.addWidget(self._lbl_s)

        lay.addWidget(self._radio_circle)
        lay.addLayout(t_col, 1)

        self.set_active(is_active)

    def set_active(self, is_active: bool):
        self._radio_circle.setText("●" if is_active else "○")
        self._radio_circle.setStyleSheet(
            f"color: {'#FFD04D' if is_active else '#B0A898'}; font-size: 16px; background: transparent;"
        )
        self._lbl_t.setStyleSheet(
            f"color: #1A1C1A; font-size: 13px; font-weight: {'700' if is_active else '600'}; background: transparent;"
        )
        if is_active:
            self.setStyleSheet(
                "ClickableCard, RadioSelectionCard{"
                "background-color: #FEF9E7; border: 1.5px solid #FFD04D; border-radius: 10px;"
                "}"
            )
        else:
            self.setStyleSheet(
                "ClickableCard, RadioSelectionCard{"
                "background-color: #FFFDF8; border: 1px solid #EDD89A; border-radius: 10px;"
                "}"
                "ClickableCard:hover, RadioSelectionCard:hover{"
                "background-color: #FAF4E6;"
                "}"
            )


# ── Option Card for Quiz Questions ─────────────────────────────────────────────

class QuizOptionCard(ClickableCard):
    """Option card (A/B/C/D) matching Warm DBMS Quiz Dashboard mockup."""

    def __init__(self, key: str, text: str = "", is_checked: bool = False, parent=None):
        super().__init__(parent)
        self.key = key
        self.setFixedHeight(54)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 8, 16, 8)
        lay.setSpacing(14)

        self._badge = QLabel(key)
        self._badge.setFixedSize(26, 26)
        self._badge.setAlignment(Qt.AlignCenter)

        self._lbl = QLabel(text)
        self._lbl.setWordWrap(True)

        lay.addWidget(self._badge)
        lay.addWidget(self._lbl, 1)

        self.set_state(text, is_checked)

    def set_state(self, text: str, is_checked: bool):
        self._lbl.setText(text)
        if is_checked:
            self._badge.setStyleSheet(
                "background-color: #FFD04D; color: #1A1C1A; border-radius: 13px; font-weight: bold; font-size: 12px;"
            )
            self._lbl.setStyleSheet("color: #1A1C1A; font-size: 13px; font-weight: 700; background: transparent;")
            self.setStyleSheet(
                "QuizOptionCard{"
                "background-color: #FEF9E7; border: 1.5px solid #FFD04D; border-radius: 12px;"
                "}"
            )
        else:
            self._badge.setStyleSheet(
                "background-color: #E8DCB8; color: #5A5445; border-radius: 13px; font-weight: bold; font-size: 12px;"
            )
            self._lbl.setStyleSheet("color: #1A1C1A; font-size: 13px; font-weight: 500; background: transparent;")
            self.setStyleSheet(
                "QuizOptionCard{"
                "background-color: #FFFDF8; border: 1px solid #EDD89A; border-radius: 12px;"
                "}"
                "QuizOptionCard:hover{"
                "background-color: #FAF4E6;"
                "}"
            )


# ── Circular Progress Widget for Results ────────────────────────────────────────

class CircularProgressGauge(QWidget):
    """Draws a crisp circular percentage gauge matching the mockup."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(76, 76)
        self._value = 80

    def setValue(self, val: int):
        self._value = max(0, min(100, val))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(6, 6, -6, -6)
        pen_bg = QPen(QColor("#E8DCB8"), 7, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen_bg)
        painter.drawArc(rect, 0, 360 * 16)

        color_chunk = QColor("#2E7D32") if self._value >= 70 else (QColor("#F57C00") if self._value >= 50 else QColor("#D32F2F"))
        pen_chunk = QPen(color_chunk, 7, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen_chunk)
        span = int(-self._value * 3.6 * 16)
        painter.drawArc(rect, 90 * 16, span)

        painter.setPen(QColor("#1A1C1A"))
        font = QFont("Segoe UI", 11)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, f"{self._value}%")


# ── 1. QuizConfigForm ──────────────────────────────────────────────────────────

class QuizConfigForm(QWidget):
    """Quiz configuration dashboard matching 'NotepadLLM Quiz Configuration Dashboard.png'."""

    generateRequested = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("QuizConfigForm{background-color: #FFF8EC; border-radius: 16px;}")

        self._doc_name: str = "Database Systems - Chapter 1.pdf"
        self._total_pages: int = 20
        self._current_page: int = 1

        self._selected_scope: str = "entire"
        self._selected_qtype: str = "mcq"
        self._selected_num_q: int = 10
        self._selected_diff: str = "Medium"
        self._selected_obj: str = "Memorization"
        self._time_limit_enabled: bool = True

        root = QHBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 22)
        root.setSpacing(22)

        # ── Left: Main Configuration Form (Scrollable) ─────────────────────────
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.NoFrame)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_scroll.setStyleSheet("QScrollArea{background: transparent; border: none;}")

        left_container = QWidget()
        left_container.setStyleSheet("background: transparent;")
        form_lay = QVBoxLayout(left_container)
        form_lay.setContentsMargins(0, 0, 10, 0)
        form_lay.setSpacing(16)

        # Header
        hdr = QHBoxLayout()
        hdr.setSpacing(14)
        badge = QFrame()
        badge.setFixedSize(44, 44)
        badge.setStyleSheet("background-color: #FFD04D; border-radius: 12px;")
        b_lay = QVBoxLayout(badge)
        b_lay.setContentsMargins(0, 0, 0, 0)
        b_lbl = QLabel("🎓")
        b_lbl.setAlignment(Qt.AlignCenter)
        b_lbl.setStyleSheet("font-size: 22px; background: transparent;")
        b_lay.addWidget(b_lbl)

        hdr_info = QVBoxLayout()
        hdr_info.setSpacing(2)
        lbl_title = QLabel("Quiz Configuration")
        lbl_title.setStyleSheet("color: #1A1C1A; font-size: 22px; font-weight: 800; font-family: 'Segoe UI', sans-serif;")
        lbl_sub = QLabel("Choose your document and customize the quiz settings.")
        lbl_sub.setStyleSheet("color: #7A7465; font-size: 13px;")
        hdr_info.addWidget(lbl_title)
        hdr_info.addWidget(lbl_sub)

        hdr.addWidget(badge)
        hdr.addLayout(hdr_info, 1)
        form_lay.addLayout(hdr)

        # Section 1: Select Source Document
        form_lay.addWidget(self._make_section_title("1. Select Source Document"))
        doc_card = QFrame()
        doc_card.setStyleSheet("background-color: #FFFDF8; border: 1px solid #EDD89A; border-radius: 12px;")
        dc_lay = QHBoxLayout(doc_card)
        dc_lay.setContentsMargins(14, 12, 14, 12)
        dc_lay.setSpacing(12)

        pdf_badge = QLabel("PDF")
        pdf_badge.setFixedSize(36, 36)
        pdf_badge.setAlignment(Qt.AlignCenter)
        pdf_badge.setStyleSheet("background-color: #E53935; color: #FFFFFF; font-weight: bold; font-size: 11px; border-radius: 6px;")

        doc_info = QVBoxLayout()
        doc_info.setSpacing(2)
        self.lbl_doc_title = QLabel(self._doc_name)
        self.lbl_doc_title.setStyleSheet("color: #1A1C1A; font-size: 13.5px; font-weight: 700; background: transparent;")
        self.lbl_doc_pages = QLabel(f"{self._total_pages} pages • 5.4 MB")
        self.lbl_doc_pages.setStyleSheet("color: #7A7465; font-size: 12px; background: transparent;")
        doc_info.addWidget(self.lbl_doc_title)
        doc_info.addWidget(self.lbl_doc_pages)

        btn_change = QPushButton("Change")
        btn_change.setCursor(Qt.PointingHandCursor)
        btn_change.setStyleSheet(
            "QPushButton{background-color: #F6ECCF; border-radius: 8px; color: #1A1C1A;"
            "font-size: 12.5px; font-weight: 600; padding: 6px 14px; border: none;}"
            "QPushButton:hover{background-color: #EEDBBA;}"
        )

        dc_lay.addWidget(pdf_badge)
        dc_lay.addLayout(doc_info, 1)
        dc_lay.addWidget(btn_change)
        form_lay.addWidget(doc_card)

        # Two-Column Form Grid
        grid_row = QHBoxLayout()
        grid_row.setSpacing(16)

        # Col 1: Choose Content & Question Type
        col1 = QVBoxLayout()
        col1.setSpacing(14)

        col1.addWidget(self._make_section_title("2. Choose Content"))
        self.card_scope_entire = RadioSelectionCard("Entire document", "Generate questions from the whole document", True)
        self.card_scope_chap = RadioSelectionCard("Specific chapter", "Select a chapter or section", False)
        self.card_scope_custom = RadioSelectionCard("Custom pages", "Enter page range (e.g. 1-10, 15-20)", False)

        self.card_scope_entire.clicked.connect(lambda: self._set_scope("entire"))
        self.card_scope_chap.clicked.connect(lambda: self._set_scope("chapter"))
        self.card_scope_custom.clicked.connect(lambda: self._set_scope("custom"))

        col1.addWidget(self.card_scope_entire)
        col1.addWidget(self.card_scope_chap)
        col1.addWidget(self.card_scope_custom)

        col1.addWidget(self._make_section_title("5. Question Type"))
        self.card_qt_mcq = RadioSelectionCard("Multiple choice (MCQ)", "4 options (A, B, C, D)", True)
        self.card_qt_tf = RadioSelectionCard("True / False", "Two options (True / False)", False)
        self.card_qt_sa = RadioSelectionCard("Short answer", "Open ended questions", False)

        self.card_qt_mcq.clicked.connect(lambda: self._set_qtype("mcq"))
        self.card_qt_tf.clicked.connect(lambda: self._set_qtype("tf"))
        self.card_qt_sa.clicked.connect(lambda: self._set_qtype("sa"))

        col1.addWidget(self.card_qt_mcq)
        col1.addWidget(self.card_qt_tf)
        col1.addWidget(self.card_qt_sa)
        col1.addStretch(1)

        grid_row.addLayout(col1, 1)

        # Col 2: Number of questions, Difficulty, Learning Objective, Time Limit
        col2 = QVBoxLayout()
        col2.setSpacing(14)

        col2.addWidget(self._make_section_title("3. Number of Questions"))
        num_row = QHBoxLayout()
        num_row.setSpacing(6)
        self.num_btns = {}
        for n in [5, 10, 15, 20]:
            btn = self._make_pill_btn(str(n), is_active=(n == 10))
            btn.clicked.connect(lambda _, val=n: self._set_num_questions(val))
            self.num_btns[str(n)] = btn
            num_row.addWidget(btn)
        btn_cust = self._make_pill_btn("Custom", is_active=False)
        self.num_btns["Custom"] = btn_cust
        num_row.addWidget(btn_cust)
        col2.addLayout(num_row)

        col2.addWidget(self._make_section_title("4. Difficulty Level"))
        diff_row = QHBoxLayout()
        diff_row.setSpacing(6)
        self.diff_btns = {}
        for d in ["Easy", "Medium", "Hard", "Mixed"]:
            btn = self._make_pill_btn(d, is_active=(d == "Medium"))
            btn.clicked.connect(lambda _, val=d: self._set_difficulty(val))
            self.diff_btns[d] = btn
            diff_row.addWidget(btn)
        col2.addLayout(diff_row)

        col2.addWidget(self._make_section_title("6. Learning Objective"))
        obj_row = QHBoxLayout()
        obj_row.setSpacing(6)
        self.obj_btns = {}
        for o in ["Memorization", "Understanding", "Application"]:
            btn = self._make_pill_btn(o, is_active=(o == "Memorization"))
            btn.clicked.connect(lambda _, val=o: self._set_objective(val))
            self.obj_btns[o] = btn
            obj_row.addWidget(btn)
        col2.addLayout(obj_row)

        col2.addWidget(self._make_section_title("7. Time Limit (Optional)"))
        time_card = QFrame()
        time_card.setStyleSheet("background-color: #FFFDF8; border: 1px solid #EDD89A; border-radius: 12px;")
        tc_lay = QVBoxLayout(time_card)
        tc_lay.setContentsMargins(14, 10, 14, 10)
        tc_lay.setSpacing(8)

        tl_top = QHBoxLayout()
        tl_lbl = QLabel("Set a time limit for each question")
        tl_lbl.setStyleSheet("color: #7A7465; font-size: 12px; background: transparent;")
        self.btn_toggle_time = QPushButton("● ON")
        self.btn_toggle_time.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_time.setFixedSize(54, 26)
        self.btn_toggle_time.setStyleSheet(
            "QPushButton{background-color: #FFD04D; border-radius: 13px; color: #1A1C1A;"
            "font-size: 11px; font-weight: bold; border: none;}"
            "QPushButton:hover{background-color: #E8B93A;}"
        )
        self.btn_toggle_time.clicked.connect(self._toggle_time_limit)
        tl_top.addWidget(tl_lbl)
        tl_top.addStretch(1)
        tl_top.addWidget(self.btn_toggle_time)
        tc_lay.addLayout(tl_top)

        self.time_combo = QComboBox()
        self.time_combo.addItems([
            "1 minute per question",
            "30 seconds per question",
            "45 seconds per question",
            "2 minutes per question"
        ])
        self.time_combo.setStyleSheet(
            "QComboBox{background-color: #FCF6EC; border: 1px solid #E8DCB8; border-radius: 8px;"
            "padding: 6px 10px; font-size: 12.5px; color: #1A1C1A;}"
            "QComboBox::drop-down{border: none;}"
        )
        self.time_combo.currentIndexChanged.connect(self._update_summary)
        tc_lay.addWidget(self.time_combo)
        col2.addWidget(time_card)
        col2.addStretch(1)

        grid_row.addLayout(col2, 1)
        form_lay.addLayout(grid_row)

        # Big Generate Quiz Button
        self.btn_generate = QPushButton("✦  Generate Quiz  ›")
        self.btn_generate.setFixedHeight(48)
        self.btn_generate.setCursor(Qt.PointingHandCursor)
        self.btn_generate.setStyleSheet(
            "QPushButton{background-color: #FFD04D; border-radius: 12px; color: #1A1C1A;"
            "font-size: 15px; font-weight: 700; border: none;}"
            "QPushButton:hover{background-color: #E8B93A;}"
            "QPushButton:pressed{background-color: #D4A017;}"
        )
        self.btn_generate.clicked.connect(self._on_generate_clicked)
        form_lay.addWidget(self.btn_generate)

        left_scroll.setWidget(left_container)
        root.addWidget(left_scroll, 62)

        # ── Right: Quiz Summary Sidebar ────────────────────────────────────────
        right_panel = QFrame()
        right_panel.setStyleSheet("background-color: #FFFDF8; border: 1px solid #EDD89A; border-radius: 16px;")
        rp_lay = QVBoxLayout(right_panel)
        rp_lay.setContentsMargins(18, 16, 18, 16)
        rp_lay.setSpacing(14)

        # Summary Header
        sum_hdr = QHBoxLayout()
        lbl_s_icon = QLabel("📄")
        lbl_s_title = QLabel("Quiz Summary")
        lbl_s_title.setStyleSheet("color: #1A1C1A; font-size: 15px; font-weight: 700; background: transparent;")
        sum_hdr.addWidget(lbl_s_icon)
        sum_hdr.addWidget(lbl_s_title)
        sum_hdr.addStretch(1)
        rp_lay.addLayout(sum_hdr)

        # Doc miniature
        doc_mini = QFrame()
        doc_mini.setStyleSheet("background-color: #FCF6EC; border-radius: 10px; padding: 6px;")
        dm_lay = QHBoxLayout(doc_mini)
        dm_lay.setContentsMargins(8, 6, 8, 6)
        dm_lay.setSpacing(8)
        pdf_mini_b = QLabel("PDF")
        pdf_mini_b.setFixedSize(26, 26)
        pdf_mini_b.setAlignment(Qt.AlignCenter)
        pdf_mini_b.setStyleSheet("background-color: #E53935; color: #FFFFFF; font-weight: bold; font-size: 9px; border-radius: 4px;")
        dm_info = QVBoxLayout()
        dm_info.setSpacing(1)
        self.lbl_sum_doc = QLabel(self._doc_name)
        self.lbl_sum_doc.setStyleSheet("color: #1A1C1A; font-size: 12px; font-weight: 600; background: transparent;")
        self.lbl_sum_pages = QLabel(f"{self._total_pages} pages • 5.4 MB")
        self.lbl_sum_pages.setStyleSheet("color: #7A7465; font-size: 11px; background: transparent;")
        dm_info.addWidget(self.lbl_sum_doc)
        dm_info.addWidget(self.lbl_sum_pages)
        dm_lay.addWidget(pdf_mini_b)
        dm_lay.addLayout(dm_info, 1)
        rp_lay.addWidget(doc_mini)

        # Summary rows
        self.lbl_sum_content = QLabel("Entire document")
        self.lbl_sum_num = QLabel("10")
        self.lbl_sum_diff = QLabel("Medium")
        self.lbl_sum_type = QLabel("Multiple choice (MCQ)")
        self.lbl_sum_obj = QLabel("Memorization")
        self.lbl_sum_time = QLabel("1 minute per question")

        rp_lay.addLayout(self._make_sum_row("📄", "Content", self.lbl_sum_content))
        rp_lay.addLayout(self._make_sum_row("❓", "Number of questions", self.lbl_sum_num))
        rp_lay.addLayout(self._make_sum_row("🧭", "Difficulty level", self.lbl_sum_diff))
        rp_lay.addLayout(self._make_sum_row("❓", "Question type", self.lbl_sum_type))
        rp_lay.addLayout(self._make_sum_row("💡", "Learning objective", self.lbl_sum_obj))
        rp_lay.addLayout(self._make_sum_row("🕒", "Time limit", self.lbl_sum_time))

        # Tip card
        tip_card = QFrame()
        tip_card.setStyleSheet("background-color: #FEF9E7; border: 1px solid #F5E5B8; border-radius: 12px;")
        tc_lay2 = QVBoxLayout(tip_card)
        tc_lay2.setContentsMargins(12, 10, 12, 10)
        tc_lay2.setSpacing(4)
        t_head = QHBoxLayout()
        t_icon = QLabel("💡")
        t_title = QLabel("Tip")
        t_title.setStyleSheet("color: #1A1C1A; font-size: 12.5px; font-weight: 700; background: transparent;")
        t_head.addWidget(t_icon)
        t_head.addWidget(t_title)
        t_head.addStretch(1)
        tc_lay2.addLayout(t_head)
        t_txt = QLabel("For better results, make sure the document has clear text and is related to a specific topic.")
        t_txt.setWordWrap(True)
        t_txt.setStyleSheet("color: #5A5445; font-size: 11.5px; line-height: 1.3; background: transparent;")
        tc_lay2.addWidget(t_txt)
        rp_lay.addWidget(tip_card)

        # What happens next card
        whn_card = QFrame()
        whn_card.setStyleSheet("background-color: #FCF6EC; border-radius: 12px; border: 1px solid #E8DCB8;")
        wn_lay = QVBoxLayout(whn_card)
        wn_lay.setContentsMargins(12, 10, 12, 10)
        wn_lay.setSpacing(6)
        w_head = QHBoxLayout()
        w_icon = QLabel("⚙")
        w_title = QLabel("What happens next?")
        w_title.setStyleSheet("color: #1A1C1A; font-size: 12.5px; font-weight: 700; background: transparent;")
        w_head.addWidget(w_icon)
        w_head.addWidget(w_title)
        w_head.addStretch(1)
        wn_lay.addLayout(w_head)

        steps = [
            ("1", "The AI will analyze your document content."),
            ("2", "It will generate questions based on your settings."),
            ("3", "You can then take the quiz and review detailed explanations.")
        ]
        for num_s, text_s in steps:
            s_row = QHBoxLayout()
            s_row.setSpacing(8)
            num_b = QLabel(num_s)
            num_b.setFixedSize(18, 18)
            num_b.setAlignment(Qt.AlignCenter)
            num_b.setStyleSheet("background-color: #FFD04D; color: #1A1C1A; font-size: 11px; font-weight: bold; border-radius: 9px;")
            lbl_st = QLabel(text_s)
            lbl_st.setWordWrap(True)
            lbl_st.setStyleSheet("color: #4A4538; font-size: 11px; line-height: 1.3; background: transparent;")
            s_row.addWidget(num_b, 0, Qt.AlignTop)
            s_row.addWidget(lbl_st, 1)
            wn_lay.addLayout(s_row)

        rp_lay.addWidget(whn_card)
        rp_lay.addStretch(1)

        root.addWidget(right_panel, 38)

    def _make_section_title(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #1A1C1A; font-size: 14px; font-weight: 700; background: transparent;")
        return lbl

    def _make_pill_btn(self, text: str, is_active: bool) -> QPushButton:
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(34)
        self._style_pill_btn(btn, is_active)
        return btn

    def _style_pill_btn(self, btn: QPushButton, is_active: bool):
        if is_active:
            btn.setStyleSheet(
                "QPushButton{background-color: #FFD04D; border-radius: 8px; color: #1A1C1A;"
                "font-size: 12px; font-weight: 700; border: none; padding: 4px 10px;}"
                "QPushButton:hover{background-color: #E8B93A;}"
            )
        else:
            btn.setStyleSheet(
                "QPushButton{background-color: #FCF6EC; border: 1px solid #E8DCB8; border-radius: 8px;"
                "color: #5A5445; font-size: 12px; font-weight: 500; padding: 4px 10px;}"
                "QPushButton:hover{background-color: #F7E7B5; color: #1A1C1A;}"
            )

    def _make_sum_row(self, icon: str, title: str, value_lbl: QLabel) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(6)
        ico = QLabel(icon)
        ico.setStyleSheet("font-size: 12px; background: transparent;")
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("color: #5A5445; font-size: 12px; background: transparent;")
        value_lbl.setStyleSheet("color: #1A1C1A; font-size: 12px; font-weight: 600; background: transparent;")
        row.addWidget(ico)
        row.addWidget(t_lbl)
        row.addStretch(1)
        row.addWidget(value_lbl)
        return row

    def _set_scope(self, scope: str):
        self._selected_scope = scope
        self.card_scope_entire.set_active(scope == "entire")
        self.card_scope_chap.set_active(scope == "chapter")
        self.card_scope_custom.set_active(scope == "custom")
        self._update_summary()

    def _set_qtype(self, qtype: str):
        self._selected_qtype = qtype
        self.card_qt_mcq.set_active(qtype == "mcq")
        self.card_qt_tf.set_active(qtype == "tf")
        self.card_qt_sa.set_active(qtype == "sa")
        self._update_summary()

    def _set_num_questions(self, num: int):
        self._selected_num_q = num
        for k, btn in self.num_btns.items():
            self._style_pill_btn(btn, k == str(num))
        self._update_summary()

    def _set_difficulty(self, diff: str):
        self._selected_diff = diff
        for k, btn in self.diff_btns.items():
            self._style_pill_btn(btn, k == diff)
        self._update_summary()

    def _set_objective(self, obj: str):
        self._selected_obj = obj
        for k, btn in self.obj_btns.items():
            self._style_pill_btn(btn, k == obj)
        self._update_summary()

    def _toggle_time_limit(self):
        self._time_limit_enabled = not self._time_limit_enabled
        if self._time_limit_enabled:
            self.btn_toggle_time.setText("● ON")
            self.btn_toggle_time.setStyleSheet(
                "QPushButton{background-color: #FFD04D; border-radius: 13px; color: #1A1C1A;"
                "font-size: 11px; font-weight: bold; border: none;}"
            )
            self.time_combo.setEnabled(True)
        else:
            self.btn_toggle_time.setText("○ OFF")
            self.btn_toggle_time.setStyleSheet(
                "QPushButton{background-color: #E0DACD; border-radius: 13px; color: #7A7465;"
                "font-size: 11px; font-weight: bold; border: none;}"
            )
            self.time_combo.setEnabled(False)
        self._update_summary()

    def _update_summary(self):
        scope_map = {"entire": "Entire document", "chapter": "Specific chapter", "custom": "Custom pages"}
        self.lbl_sum_content.setText(scope_map.get(self._selected_scope, "Entire document"))
        self.lbl_sum_num.setText(str(self._selected_num_q))
        self.lbl_sum_diff.setText(self._selected_diff)
        qt_map = {"mcq": "Multiple choice (MCQ)", "tf": "True / False", "sa": "Short answer"}
        self.lbl_sum_type.setText(qt_map.get(self._selected_qtype, "Multiple choice (MCQ)"))
        self.lbl_sum_obj.setText(self._selected_obj)
        if self._time_limit_enabled:
            self.lbl_sum_time.setText(self.time_combo.currentText())
        else:
            self.lbl_sum_time.setText("None")

    def update_page_info(self, current_page: int, total_pages: int, doc_name: str = ""):
        self._current_page = current_page
        self._total_pages = total_pages
        if doc_name:
            self._doc_name = doc_name
            self.lbl_doc_title.setText(doc_name)
            self.lbl_sum_doc.setText(doc_name)
        self.lbl_doc_pages.setText(f"{total_pages} pages • 5.4 MB")
        self.lbl_sum_pages.setText(f"{total_pages} pages • 5.4 MB")

    def _on_generate_clicked(self):
        page_range = (1, self._total_pages) if self._selected_scope == "entire" else (self._current_page, self._current_page)
        self.generateRequested.emit({
            "num_questions": self._selected_num_q,
            "difficulty": self._selected_diff.lower(),
            "focus": self._selected_obj.lower(),
            "page_range": page_range,
            "time_limit": self.time_combo.currentText() if self._time_limit_enabled else ""
        })


# ── 2. QuizLoadingScreen ───────────────────────────────────────────────────────

class QuizLoadingScreen(QWidget):
    """Quiz generation loading dashboard matching 'AI Quiz Generation Dashboard.png'."""

    cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("QuizLoadingScreen{background-color: #FFF8EC; border-radius: 16px;}")

        self._progress = 65
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

        root = QHBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 22)
        root.setSpacing(22)

        # ── Left: Main Animation & Checklist ──────────────────────────────────
        left_panel = QVBoxLayout()
        left_panel.setSpacing(14)

        # Header
        hdr = QHBoxLayout()
        hdr.setSpacing(14)
        badge = QFrame()
        badge.setFixedSize(44, 44)
        badge.setStyleSheet("background-color: #FFD04D; border-radius: 12px;")
        b_lay = QVBoxLayout(badge)
        b_lay.setContentsMargins(0, 0, 0, 0)
        b_lbl = QLabel("🧠")
        b_lbl.setAlignment(Qt.AlignCenter)
        b_lbl.setStyleSheet("font-size: 22px; background: transparent;")
        b_lay.addWidget(b_lbl)

        hdr_info = QVBoxLayout()
        hdr_info.setSpacing(2)
        lbl_title = QLabel("Generating your quiz...")
        lbl_title.setStyleSheet("color: #1A1C1A; font-size: 22px; font-weight: 800; font-family: 'Segoe UI', sans-serif;")
        lbl_sub = QLabel("The AI is reading your document and creating questions.")
        lbl_sub.setStyleSheet("color: #7A7465; font-size: 13px;")
        hdr_info.addWidget(lbl_title)
        hdr_info.addWidget(lbl_sub)

        hdr.addWidget(badge)
        hdr.addLayout(hdr_info, 1)
        left_panel.addLayout(hdr)

        # Center illustration (robot reading book)
        illust_frame = QFrame()
        illust_frame.setFixedHeight(120)
        illust_lay = QVBoxLayout(illust_frame)
        illust_lay.setAlignment(Qt.AlignCenter)
        lbl_bot = QLabel("🤖 📖 ✨")
        lbl_bot.setAlignment(Qt.AlignCenter)
        lbl_bot.setStyleSheet("font-size: 52px; background: transparent;")
        illust_lay.addWidget(lbl_bot)
        left_panel.addWidget(illust_frame)

        # Progress bar with percentage
        pb_row = QHBoxLayout()
        pb_row.setSpacing(12)
        self.prog_bar = QProgressBar()
        self.prog_bar.setFixedHeight(10)
        self.prog_bar.setRange(0, 100)
        self.prog_bar.setValue(65)
        self.prog_bar.setTextVisible(False)
        self.prog_bar.setStyleSheet(
            "QProgressBar{background-color: #E8DCB8; border-radius: 5px; border: none;}"
            "QProgressBar::chunk{background-color: #FFD04D; border-radius: 5px;}"
        )
        self.lbl_pct = QLabel("65%")
        self.lbl_pct.setStyleSheet("color: #1A1C1A; font-size: 14px; font-weight: 700; background: transparent;")

        pb_row.addWidget(self.prog_bar, 1)
        pb_row.addWidget(self.lbl_pct)
        left_panel.addLayout(pb_row)

        self.lbl_status = QLabel("Processing content and generating questions...")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet("color: #7A7465; font-size: 13px; font-weight: 500;")
        left_panel.addWidget(self.lbl_status)

        # Checklist card
        chk_card = QFrame()
        chk_card.setStyleSheet("background-color: #FFFDF8; border: 1px solid #EDD89A; border-radius: 14px;")
        cc_lay = QVBoxLayout(chk_card)
        cc_lay.setContentsMargins(18, 14, 18, 14)
        cc_lay.setSpacing(10)

        self.chk_items = [
            ("Reading document content", "Extracting text and identifying key topics.", "done"),
            ("Analyzing key concepts", "Finding important definitions, examples and relationships.", "done"),
            ("Creating questions", "Generating multiple choice questions (MCQ).", "done"),
            ("Validating answers", "Checking correctness and removing duplicates.", "active"),
            ("Formatting quiz", "Preparing the final quiz structure.", "pending"),
            ("Almost ready", "Finalizing your quiz...", "pending")
        ]
        self._render_checklist(cc_lay)
        left_panel.addWidget(chk_card)

        # Cancel button
        btn_cancel_row = QHBoxLayout()
        btn_cancel_row.addStretch(1)
        self.btn_cancel = QPushButton("▢  Cancel Generation")
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setStyleSheet(
            "QPushButton{background-color: #F6ECCF; border-radius: 10px; color: #1A1C1A;"
            "font-size: 13px; font-weight: 600; padding: 8px 24px; border: none;}"
            "QPushButton:hover{background-color: #EEDBBA;}"
        )
        self.btn_cancel.clicked.connect(self.cancelled.emit)
        btn_cancel_row.addWidget(self.btn_cancel)
        btn_cancel_row.addStretch(1)
        left_panel.addLayout(btn_cancel_row)

        root.addLayout(left_panel, 62)

        # ── Right: Info & Tips ────────────────────────────────────────────────
        right_panel = QFrame()
        right_panel.setStyleSheet("background-color: #FFFDF8; border: 1px solid #EDD89A; border-radius: 16px;")
        rp_lay = QVBoxLayout(right_panel)
        rp_lay.setContentsMargins(18, 16, 18, 16)
        rp_lay.setSpacing(14)

        # Doc Info
        d_head = QHBoxLayout()
        d_icon = QLabel("📄")
        d_title = QLabel("Document Information")
        d_title.setStyleSheet("color: #1A1C1A; font-size: 14px; font-weight: 700; background: transparent;")
        d_head.addWidget(d_icon)
        d_head.addWidget(d_title)
        d_head.addStretch(1)
        rp_lay.addLayout(d_head)

        mini_doc = QFrame()
        mini_doc.setStyleSheet("background-color: #FCF6EC; border-radius: 10px; padding: 6px;")
        md_lay = QHBoxLayout(mini_doc)
        md_lay.setContentsMargins(8, 6, 8, 6)
        md_lay.setSpacing(8)
        pb = QLabel("PDF")
        pb.setFixedSize(26, 26)
        pb.setAlignment(Qt.AlignCenter)
        pb.setStyleSheet("background-color: #E53935; color: #FFFFFF; font-weight: bold; font-size: 9px; border-radius: 4px;")
        md_info = QVBoxLayout()
        md_info.setSpacing(1)
        lbl_md_t = QLabel("Database Systems - Chapter 1.pdf")
        lbl_md_t.setStyleSheet("color: #1A1C1A; font-size: 12px; font-weight: 600; background: transparent;")
        lbl_md_p = QLabel("20 pages • 5.4 MB")
        lbl_md_p.setStyleSheet("color: #7A7465; font-size: 11px; background: transparent;")
        md_info.addWidget(lbl_md_t)
        md_info.addWidget(lbl_md_p)
        md_lay.addWidget(pb)
        md_lay.addLayout(md_info, 1)
        rp_lay.addWidget(mini_doc)

        rp_lay.addLayout(self._make_sum_row("📄", "Content", "Entire document"))
        rp_lay.addLayout(self._make_sum_row("❓", "Number of questions", "10"))
        rp_lay.addLayout(self._make_sum_row("🧭", "Difficulty level", "Medium"))
        rp_lay.addLayout(self._make_sum_row("❓", "Question type", "Multiple choice (MCQ)"))
        rp_lay.addLayout(self._make_sum_row("💡", "Learning objective", "Memorization"))
        rp_lay.addLayout(self._make_sum_row("🕒", "Time limit", "1 minute per question"))

        # Tips
        tips_c = QFrame()
        tips_c.setStyleSheet("background-color: #FEF9E7; border: 1px solid #F5E5B8; border-radius: 12px;")
        tc_lay = QVBoxLayout(tips_c)
        tc_lay.setContentsMargins(12, 10, 12, 10)
        tc_lay.setSpacing(6)
        th = QHBoxLayout()
        th.addWidget(QLabel("💡"))
        th.addWidget(QLabel("Tips"))
        th.addStretch(1)
        tc_lay.addLayout(th)

        tips_items = [
            "The AI is analyzing the content to create relevant questions.",
            "This may take a few moments depending on the document size.",
            "You can cancel at any time if needed."
        ]
        for tip in tips_items:
            tr = QHBoxLayout()
            tr.setSpacing(6)
            chk = QLabel("✓")
            chk.setFixedSize(16, 16)
            chk.setAlignment(Qt.AlignCenter)
            chk.setStyleSheet("background-color: #FFD04D; color: #1A1C1A; font-size: 10px; font-weight: bold; border-radius: 8px;")
            lbl = QLabel(tip)
            lbl.setWordWrap(True)
            lbl.setStyleSheet("color: #5A5445; font-size: 11.5px; background: transparent;")
            tr.addWidget(chk, 0, Qt.AlignTop)
            tr.addWidget(lbl, 1)
            tc_lay.addLayout(tr)
        rp_lay.addWidget(tips_c)

        # Did you know?
        dyk_c = QFrame()
        dyk_c.setStyleSheet("background-color: #FCF6EC; border: 1px solid #E8DCB8; border-radius: 12px;")
        dyk_lay = QVBoxLayout(dyk_c)
        dyk_lay.setContentsMargins(12, 10, 12, 10)
        dyk_lay.setSpacing(4)
        dh = QHBoxLayout()
        dh.addWidget(QLabel("🧠"))
        dh.addWidget(QLabel("Did you know?"))
        dh.addStretch(1)
        dyk_lay.addLayout(dh)
        lbl_dyk = QLabel("The AI identifies key concepts, definitions, examples and relationships to generate high-quality questions tailored to your document.")
        lbl_dyk.setWordWrap(True)
        lbl_dyk.setStyleSheet("color: #5A5445; font-size: 11px; line-height: 1.3; background: transparent;")
        dyk_lay.addWidget(lbl_dyk)
        rp_lay.addWidget(dyk_c)

        rp_lay.addStretch(1)
        root.addWidget(right_panel, 38)

    def _render_checklist(self, layout):
        for title, subtitle, state in self.chk_items:
            row = QHBoxLayout()
            row.setSpacing(10)

            badge = QLabel()
            badge.setFixedSize(22, 22)
            badge.setAlignment(Qt.AlignCenter)
            if state == "done":
                badge.setText("✓")
                badge.setStyleSheet("background-color: #FFD04D; color: #1A1C1A; font-size: 12px; font-weight: bold; border-radius: 11px;")
            elif state == "active":
                badge.setText("⌛")
                badge.setStyleSheet("background-color: #FFF3CD; color: #856404; font-size: 11px; border: 1px solid #FFEEBA; border-radius: 11px;")
            else:
                badge.setText("○")
                badge.setStyleSheet("color: #C0B8A8; font-size: 14px; background: transparent;")

            t_col = QVBoxLayout()
            t_col.setSpacing(1)
            t_lbl = QLabel(title)
            t_lbl.setStyleSheet(f"color: {'#1A1C1A' if state != 'pending' else '#8C8474'}; font-size: 12.5px; font-weight: 700; background: transparent;")
            s_lbl = QLabel(subtitle)
            s_lbl.setStyleSheet(f"color: {'#7A7465' if state != 'pending' else '#A8A090'}; font-size: 11px; background: transparent;")
            t_col.addWidget(t_lbl)
            t_col.addWidget(s_lbl)

            row.addWidget(badge)
            row.addLayout(t_col, 1)
            layout.addLayout(row)

    def _make_sum_row(self, icon: str, title: str, value: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(6)
        ico = QLabel(icon)
        ico.setStyleSheet("font-size: 12px; background: transparent;")
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("color: #5A5445; font-size: 12px; background: transparent;")
        v_lbl = QLabel(value)
        v_lbl.setStyleSheet("color: #1A1C1A; font-size: 12px; font-weight: 600; background: transparent;")
        row.addWidget(ico)
        row.addWidget(t_lbl)
        row.addStretch(1)
        row.addWidget(v_lbl)
        return row

    def start(self):
        self._progress = 20
        self.prog_bar.setValue(self._progress)
        self.lbl_pct.setText(f"{self._progress}%")
        self._timer.start(350)

    def stop(self):
        self._timer.stop()

    def _tick(self):
        if self._progress < 90:
            self._progress += 5
            self.prog_bar.setValue(self._progress)
            self.lbl_pct.setText(f"{self._progress}%")


# ── 3. QuizQuestionView ────────────────────────────────────────────────────────

class QuizQuestionView(QWidget):
    """Quiz questions dashboard matching 'Warm DBMS Quiz Dashboard.png'."""

    submitRequested = Signal(object)
    changeSettingsRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("QuizQuestionView{background-color: #FFF8EC; border-radius: 16px;}")

        self._questions: list[dict] = DEFAULT_DBMS_QUESTIONS
        self._current: int = 0
        self._answers: dict = {}
        self._timer_seconds: int = 750  # 12:30 default
        self._qtimer = QTimer(self)
        self._qtimer.timeout.connect(self._on_timer_tick)

        root = QHBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 22)
        root.setSpacing(22)

        # ── Left: Main Question Canvas ─────────────────────────────────────────
        left_panel = QVBoxLayout()
        left_panel.setSpacing(14)

        # Header
        hdr = QHBoxLayout()
        hdr.setSpacing(14)
        badge = QFrame()
        badge.setFixedSize(44, 44)
        badge.setStyleSheet("background-color: #FFD04D; border-radius: 12px;")
        b_lay = QVBoxLayout(badge)
        b_lay.setContentsMargins(0, 0, 0, 0)
        b_lbl = QLabel("🎓")
        b_lbl.setAlignment(Qt.AlignCenter)
        b_lbl.setStyleSheet("font-size: 22px; background: transparent;")
        b_lay.addWidget(b_lbl)

        hdr_info = QVBoxLayout()
        hdr_info.setSpacing(2)
        self.lbl_quiz_title = QLabel("DBMS Quiz")
        self.lbl_quiz_title.setStyleSheet("color: #1A1C1A; font-size: 20px; font-weight: 800; font-family: 'Segoe UI', sans-serif;")
        lbl_sub = QLabel("Test your knowledge from the current document.")
        lbl_sub.setStyleSheet("color: #7A7465; font-size: 13px;")
        hdr_info.addWidget(self.lbl_quiz_title)
        hdr_info.addWidget(lbl_sub)

        # Timer
        timer_col = QVBoxLayout()
        timer_col.setSpacing(1)
        timer_col.setAlignment(Qt.AlignCenter)
        lbl_t_tag = QLabel("🕒 Time (optional)")
        lbl_t_tag.setStyleSheet("color: #7A7465; font-size: 11px;")
        self.lbl_timer = QLabel("00:12:30")
        self.lbl_timer.setStyleSheet("color: #1A1C1A; font-size: 14px; font-weight: 700;")
        timer_col.addWidget(lbl_t_tag)
        timer_col.addWidget(self.lbl_timer)

        btn_chg = QPushButton("⚙ Change Settings")
        btn_chg.setCursor(Qt.PointingHandCursor)
        btn_chg.setStyleSheet(
            "QPushButton{background-color: #F6ECCF; border-radius: 8px; color: #1A1C1A;"
            "font-size: 12px; font-weight: 600; padding: 7px 12px; border: none;}"
            "QPushButton:hover{background-color: #EEDBBA;}"
        )
        btn_chg.clicked.connect(self.changeSettingsRequested.emit)

        hdr.addWidget(badge)
        hdr.addLayout(hdr_info, 1)
        hdr.addLayout(timer_col)
        hdr.addSpacing(10)
        hdr.addWidget(btn_chg)
        left_panel.addLayout(hdr)

        # Main Progress Bar
        prog_row = QHBoxLayout()
        prog_row.setSpacing(10)
        self.main_progress = QProgressBar()
        self.main_progress.setFixedHeight(8)
        self.main_progress.setTextVisible(False)
        self.main_progress.setStyleSheet(
            "QProgressBar{background-color: #E8DCB8; border-radius: 4px; border: none;}"
            "QProgressBar::chunk{background-color: #FFD04D; border-radius: 4px;}"
        )
        self.lbl_q_fraction = QLabel("1 / 10")
        self.lbl_q_fraction.setStyleSheet("color: #1A1C1A; font-size: 13px; font-weight: 700; background: transparent;")
        prog_row.addWidget(self.main_progress, 1)
        prog_row.addWidget(self.lbl_q_fraction)
        left_panel.addLayout(prog_row)

        # Question Card
        q_card = QFrame()
        q_card.setStyleSheet("background-color: #FFFDF8; border: 1px solid #EDD89A; border-radius: 16px;")
        qc_lay = QVBoxLayout(q_card)
        qc_lay.setContentsMargins(20, 16, 20, 16)
        qc_lay.setSpacing(14)

        # Tag Pills row
        tags_row = QHBoxLayout()
        tags_row.setSpacing(8)
        self.lbl_pill_qnum = QLabel("Question 1")
        self.lbl_pill_qnum.setStyleSheet("background-color: #F6ECCF; border-radius: 6px; padding: 3px 8px; color: #1A1C1A; font-size: 11.5px; font-weight: 600;")
        self.lbl_pill_diff = QLabel("📊 Medium")
        self.lbl_pill_diff.setStyleSheet("background-color: #FFF3CD; border-radius: 6px; padding: 3px 8px; color: #856404; font-size: 11.5px; font-weight: 600;")
        self.lbl_pill_src = QLabel("📄 Source: Page 5")
        self.lbl_pill_src.setStyleSheet("color: #7A7465; font-size: 12px; background: transparent;")

        tags_row.addWidget(self.lbl_pill_qnum)
        tags_row.addWidget(self.lbl_pill_diff)
        tags_row.addStretch(1)
        tags_row.addWidget(self.lbl_pill_src)
        qc_lay.addLayout(tags_row)

        # Question Text
        self.lbl_question = QLabel("Which component stores data physically?")
        self.lbl_question.setWordWrap(True)
        self.lbl_question.setStyleSheet("color: #1A1C1A; font-size: 16px; font-weight: 700; line-height: 1.4; background: transparent;")
        qc_lay.addWidget(self.lbl_question)

        # 4 Option Cards
        self.opt_cards: dict[str, QuizOptionCard] = {}
        for key in ["A", "B", "C", "D"]:
            card = QuizOptionCard(key, "", False)
            card.clicked.connect(lambda k=key: self._select_option(k))
            self.opt_cards[key] = card
            qc_lay.addWidget(card)

        left_panel.addWidget(q_card, 1)

        # Bottom Navigation
        nav_row = QHBoxLayout()
        self.btn_prev = QPushButton("‹  Previous")
        self.btn_prev.setCursor(Qt.PointingHandCursor)
        self.btn_prev.setStyleSheet(
            "QPushButton{background-color: #F6ECCF; border-radius: 10px; color: #1A1C1A;"
            "font-size: 13px; font-weight: 600; padding: 10px 22px; border: none;}"
            "QPushButton:hover{background-color: #EEDBBA;}"
            "QPushButton:disabled{color: #B0A898; background-color: #F2E8CB;}"
        )
        self.btn_prev.clicked.connect(self._prev)

        self.btn_next = QPushButton("Next  ›")
        self.btn_next.setCursor(Qt.PointingHandCursor)
        self.btn_next.setStyleSheet(
            "QPushButton{background-color: #FFD04D; border-radius: 10px; color: #1A1C1A;"
            "font-size: 13px; font-weight: 700; padding: 10px 26px; border: none;}"
            "QPushButton:hover{background-color: #E8B93A;}"
        )
        self.btn_next.clicked.connect(self._next)

        self.btn_submit = QPushButton("✔  Submit Quiz")
        self.btn_submit.setCursor(Qt.PointingHandCursor)
        self.btn_submit.setStyleSheet(
            "QPushButton{background-color: #FFD04D; border-radius: 10px; color: #1A1C1A;"
            "font-size: 13px; font-weight: 700; padding: 10px 26px; border: none;}"
            "QPushButton:hover{background-color: #E8B93A;}"
        )
        self.btn_submit.clicked.connect(self._submit)
        self.btn_submit.hide()

        nav_row.addWidget(self.btn_prev)
        nav_row.addStretch(1)
        nav_row.addWidget(self.btn_next)
        nav_row.addWidget(self.btn_submit)
        left_panel.addLayout(nav_row)

        root.addLayout(left_panel, 62)

        # ── Right: Questions Sidebar ──────────────────────────────────────────
        right_panel = QFrame()
        right_panel.setStyleSheet("background-color: #FFFDF8; border: 1px solid #EDD89A; border-radius: 16px;")
        rp_lay = QVBoxLayout(right_panel)
        rp_lay.setContentsMargins(18, 16, 18, 16)
        rp_lay.setSpacing(14)

        # Top tab pills
        tabs_row = QHBoxLayout()
        tabs_row.setSpacing(6)
        btn_tab_q = QPushButton("📄 Questions")
        btn_tab_q.setStyleSheet("background-color: #FFD04D; border-radius: 8px; color: #1A1C1A; font-size: 12px; font-weight: 700; padding: 6px 12px; border: none;")
        btn_tab_r = QPushButton("📊 Results")
        btn_tab_r.setStyleSheet("background-color: transparent; border-radius: 8px; color: #5A5445; font-size: 12px; padding: 6px 10px; border: none;")
        btn_tab_s = QPushButton("⚙ Settings")
        btn_tab_s.setStyleSheet("background-color: transparent; border-radius: 8px; color: #5A5445; font-size: 12px; padding: 6px 10px; border: none;")
        tabs_row.addWidget(btn_tab_q)
        tabs_row.addWidget(btn_tab_r)
        tabs_row.addWidget(btn_tab_s)
        rp_lay.addLayout(tabs_row)

        # Quiz Progress Card
        prog_card = QFrame()
        prog_card.setStyleSheet("background-color: #FCF6EC; border: 1px solid #E8DCB8; border-radius: 12px;")
        pc_lay = QVBoxLayout(prog_card)
        pc_lay.setContentsMargins(14, 12, 14, 12)
        pc_lay.setSpacing(8)

        pc_head = QHBoxLayout()
        pc_title = QLabel("Quiz Progress")
        pc_title.setStyleSheet("color: #1A1C1A; font-size: 13px; font-weight: 700; background: transparent;")
        self.lbl_pc_fraction = QLabel("1 / 10")
        self.lbl_pc_fraction.setStyleSheet("color: #7A7465; font-size: 12px; font-weight: 600; background: transparent;")
        pc_head.addWidget(pc_title)
        pc_head.addStretch(1)
        pc_head.addWidget(self.lbl_pc_fraction)
        pc_lay.addLayout(pc_head)

        self.side_bar = QProgressBar()
        self.side_bar.setFixedHeight(6)
        self.side_bar.setTextVisible(False)
        self.side_bar.setStyleSheet(
            "QProgressBar{background-color: #E8DCB8; border-radius: 3px; border: none;}"
            "QProgressBar::chunk{background-color: #FFD04D; border-radius: 3px;}"
        )
        pc_lay.addWidget(self.side_bar)

        # Circle steps row (1 to 10)
        self.step_circles: list[QLabel] = []
        circle_row = QHBoxLayout()
        circle_row.setSpacing(4)
        for i in range(10):
            lbl_c = QLabel(str(i + 1))
            lbl_c.setFixedSize(22, 22)
            lbl_c.setAlignment(Qt.AlignCenter)
            lbl_c.setStyleSheet("background-color: #E8DCB8; color: #5A5445; border-radius: 11px; font-size: 10px; font-weight: bold;")
            self.step_circles.append(lbl_c)
            circle_row.addWidget(lbl_c)
        pc_lay.addLayout(circle_row)
        rp_lay.addWidget(prog_card)

        # All Questions List (Scrollable)
        lbl_all_q = QLabel("All Questions")
        lbl_all_q.setStyleSheet("color: #1A1C1A; font-size: 13.5px; font-weight: 700; background: transparent;")
        rp_lay.addWidget(lbl_all_q)

        all_q_scroll = QScrollArea()
        all_q_scroll.setWidgetResizable(True)
        all_q_scroll.setFrameShape(QFrame.NoFrame)
        all_q_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        all_q_scroll.setStyleSheet("QScrollArea{background: transparent; border: none;}")

        self.all_q_container = QWidget()
        self.all_q_container.setStyleSheet("background: transparent;")
        self.all_q_lay = QVBoxLayout(self.all_q_container)
        self.all_q_lay.setContentsMargins(0, 0, 4, 0)
        self.all_q_lay.setSpacing(6)

        all_q_scroll.setWidget(self.all_q_container)
        rp_lay.addWidget(all_q_scroll, 1)

        root.addWidget(right_panel, 38)

    def load_questions(self, questions: list[dict]):
        self._questions = questions or DEFAULT_DBMS_QUESTIONS
        self._current = 0
        self._answers = {}
        self.main_progress.setRange(0, len(self._questions))
        self.side_bar.setRange(0, len(self._questions))
        self._timer_seconds = len(self._questions) * 60
        self._qtimer.start(1000)
        self._render()

    def _render(self):
        n = len(self._questions)
        idx = self._current
        q = self._questions[idx]

        self.lbl_q_fraction.setText(f"{idx + 1} / {n}")
        self.lbl_pc_fraction.setText(f"{idx + 1} / {n}")
        self.main_progress.setValue(idx + 1)
        self.side_bar.setValue(idx + 1)

        self.lbl_pill_qnum.setText(f"Question {idx + 1}")
        self.lbl_pill_src.setText(f"📄 Source: Page {q.get('page', idx + 1)}")
        self.lbl_question.setText(q["question"])

        # Render options
        chosen = self._answers.get(idx, "")
        for key in ["A", "B", "C", "D"]:
            card = self.opt_cards[key]
            text = q["options"].get(key, "")
            is_checked = (chosen == key)
            card.set_state(text, is_checked)

        self.btn_prev.setEnabled(idx > 0)
        self.btn_next.setVisible(idx < n - 1)
        self.btn_submit.setVisible(idx == n - 1)

        # Update circle step indicators
        for i, lbl_c in enumerate(self.step_circles):
            if i >= n:
                lbl_c.hide()
                continue
            lbl_c.show()
            if i in self._answers:
                lbl_c.setText("✓")
                lbl_c.setStyleSheet("background-color: #2E7D32; color: #FFFFFF; border-radius: 11px; font-size: 10px; font-weight: bold;")
            elif i == idx:
                lbl_c.setText(str(i + 1))
                lbl_c.setStyleSheet("background-color: #FFD04D; color: #1A1C1A; border-radius: 11px; font-size: 10px; font-weight: bold;")
            else:
                lbl_c.setText(str(i + 1))
                lbl_c.setStyleSheet("background-color: #E8DCB8; color: #5A5445; border-radius: 11px; font-size: 10px; font-weight: bold;")

        # Render all questions list
        _clear_layout(self.all_q_lay)
        for i, q_item in enumerate(self._questions):
            btn_q = QPushButton()
            btn_q.setCursor(Qt.PointingHandCursor)
            btn_q.setFixedHeight(38)

            q_row = QHBoxLayout(btn_q)
            q_row.setContentsMargins(8, 4, 8, 4)
            q_row.setSpacing(8)

            c_lbl = QLabel(str(i + 1))
            c_lbl.setFixedSize(20, 20)
            c_lbl.setAlignment(Qt.AlignCenter)
            if i in self._answers:
                c_lbl.setText("✓")
                c_lbl.setStyleSheet("background-color: #2E7D32; color: #FFFFFF; border-radius: 10px; font-size: 10px; font-weight: bold;")
            elif i == idx:
                c_lbl.setStyleSheet("background-color: #FFD04D; color: #1A1C1A; border-radius: 10px; font-size: 10px; font-weight: bold;")
            else:
                c_lbl.setStyleSheet("background-color: #E8DCB8; color: #5A5445; border-radius: 10px; font-size: 10px; font-weight: bold;")

            t_lbl = QLabel(q_item["question"][:36] + ("..." if len(q_item["question"]) > 36 else ""))
            t_lbl.setStyleSheet(f"color: #1A1C1A; font-size: 11.5px; font-weight: {'700' if i == idx else '500'}; background: transparent;")

            chev = QLabel("›" if i != idx else "•")
            chev.setStyleSheet("color: #8C8474; font-size: 12px; font-weight: bold; background: transparent;")

            q_row.addWidget(c_lbl)
            q_row.addWidget(t_lbl, 1)
            q_row.addWidget(chev)

            if i == idx:
                btn_q.setStyleSheet("QPushButton{background-color: #FEF9E7; border: 1px solid #FFD04D; border-radius: 8px;}")
            else:
                btn_q.setStyleSheet("QPushButton{background-color: #FCF6EC; border: 1px solid #E8DCB8; border-radius: 8px;}"
                                    "QPushButton:hover{background-color: #F6ECCF;}")

            btn_q.clicked.connect(lambda _, target=i: self._jump_to_question(target))
            self.all_q_lay.addWidget(btn_q)

        self.all_q_lay.addStretch(1)

    def _select_option(self, key: str):
        self._answers[self._current] = key
        self._render()

    def _jump_to_question(self, index: int):
        self._current = index
        self._render()

    def _prev(self):
        if self._current > 0:
            self._current -= 1
            self._render()

    def _next(self):
        if self._current < len(self._questions) - 1:
            self._current += 1
            self._render()

    def _submit(self):
        self._qtimer.stop()
        self.submitRequested.emit(self._answers)

    def _on_timer_tick(self):
        if self._timer_seconds > 0:
            self._timer_seconds -= 1
            m = self._timer_seconds // 60
            s = self._timer_seconds % 60
            self.lbl_timer.setText(f"00:{m:02d}:{s:02d}")


# ── 4. QuizResultsView ─────────────────────────────────────────────────────────

class QuizResultsView(QWidget):
    """Quiz results dashboard matching 'NotepadLLM Quiz Results Dashboard.png'."""

    retryRequested = Signal()
    backToDocRequested = Signal()
    openPageRequested = Signal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("QuizResultsView{background-color: #FFF8EC; border-radius: 16px;}")

        self._questions: list[dict] = DEFAULT_DBMS_QUESTIONS
        self._answers: dict = {}
        self._doc_name: str = "Database Systems - Chapter 1.pdf"
        self._filter_mode: str = "all"  # "all", "correct", "incorrect"

        root = QHBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 22)
        root.setSpacing(22)

        # ── Left: Score Strip & Question Reviews ───────────────────────────────
        left_panel = QVBoxLayout()
        left_panel.setSpacing(14)

        # Header
        hdr = QHBoxLayout()
        hdr.setSpacing(14)
        badge = QFrame()
        badge.setFixedSize(44, 44)
        badge.setStyleSheet("background-color: #FFD04D; border-radius: 12px;")
        b_lay = QVBoxLayout(badge)
        b_lay.setContentsMargins(0, 0, 0, 0)
        b_lbl = QLabel("🏆")
        b_lbl.setAlignment(Qt.AlignCenter)
        b_lbl.setStyleSheet("font-size: 22px; background: transparent;")
        b_lay.addWidget(b_lbl)

        hdr_info = QVBoxLayout()
        hdr_info.setSpacing(2)
        lbl_title = QLabel("Quiz Completed!")
        lbl_title.setStyleSheet("color: #1A1C1A; font-size: 20px; font-weight: 800; font-family: 'Segoe UI', sans-serif;")
        lbl_sub = QLabel("Here are your results and detailed explanations.")
        lbl_sub.setStyleSheet("color: #7A7465; font-size: 13px;")
        hdr_info.addWidget(lbl_title)
        hdr_info.addWidget(lbl_sub)

        hdr.addWidget(badge)
        hdr.addLayout(hdr_info, 1)

        # Action buttons
        btn_rev_all = QPushButton("📄 Review All")
        btn_rev_all.setCursor(Qt.PointingHandCursor)
        btn_rev_all.setStyleSheet(
            "QPushButton{background-color: #F6ECCF; border-radius: 8px; color: #1A1C1A;"
            "font-size: 12px; font-weight: 600; padding: 7px 12px; border: none;}"
            "QPushButton:hover{background-color: #EEDBBA;}"
        )

        btn_try = QPushButton("↺ Try Again")
        btn_try.setCursor(Qt.PointingHandCursor)
        btn_try.setStyleSheet(
            "QPushButton{background-color: #FFD04D; border-radius: 8px; color: #1A1C1A;"
            "font-size: 12px; font-weight: 700; padding: 7px 14px; border: none;}"
            "QPushButton:hover{background-color: #E8B93A;}"
        )
        btn_try.clicked.connect(self.retryRequested.emit)

        btn_back = QPushButton("📄 Back to Document")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setStyleSheet(
            "QPushButton{background-color: #F6ECCF; border-radius: 8px; color: #1A1C1A;"
            "font-size: 12px; font-weight: 600; padding: 7px 12px; border: none;}"
            "QPushButton:hover{background-color: #EEDBBA;}"
        )
        btn_back.clicked.connect(self.backToDocRequested.emit)

        hdr.addWidget(btn_rev_all)
        hdr.addWidget(btn_try)
        hdr.addWidget(btn_back)
        left_panel.addLayout(hdr)

        # 5 Score Cards Row
        score_strip = QHBoxLayout()
        score_strip.setSpacing(10)

        # Card 1: Circular gauge
        gauge_card = QFrame()
        gauge_card.setStyleSheet("background-color: #FFFDF8; border: 1px solid #EDD89A; border-radius: 12px;")
        gc_lay = QHBoxLayout(gauge_card)
        gc_lay.setContentsMargins(12, 10, 12, 10)
        gc_lay.setSpacing(10)
        self.gauge = CircularProgressGauge()
        gc_info = QVBoxLayout()
        gc_info.setSpacing(1)
        lbl_sc_tag = QLabel("Score")
        lbl_sc_tag.setStyleSheet("color: #7A7465; font-size: 11px;")
        self.lbl_score_ratio = QLabel("8 / 10")
        self.lbl_score_ratio.setStyleSheet("color: #1A1C1A; font-size: 16px; font-weight: 800;")
        lbl_ca = QLabel("Correct answers")
        lbl_ca.setStyleSheet("color: #7A7465; font-size: 11px;")
        gc_info.addWidget(lbl_sc_tag)
        gc_info.addWidget(self.lbl_score_ratio)
        gc_info.addWidget(lbl_ca)
        gc_lay.addWidget(self.gauge)
        gc_lay.addLayout(gc_info)
        score_strip.addWidget(gauge_card, 2)

        # Card 2: Correct
        c_card = self._make_stat_card("✓", "#2E7D32", "#E8F5E9", "#A5D6A7")
        self.lbl_stat_c_num = QLabel("8")
        self.lbl_stat_c_num.setStyleSheet("color: #2E7D32; font-size: 18px; font-weight: 800; background: transparent;")
        lbl_c_tag = QLabel("Correct")
        lbl_c_tag.setStyleSheet("color: #2E7D32; font-size: 11.5px; font-weight: 600; background: transparent;")
        c_card.layout().addWidget(self.lbl_stat_c_num)
        c_card.layout().addWidget(lbl_c_tag)
        score_strip.addWidget(c_card, 1)

        # Card 3: Incorrect
        inc_card = self._make_stat_card("✕", "#C62828", "#FFEBEE", "#EF9A9A")
        self.lbl_stat_inc_num = QLabel("2")
        self.lbl_stat_inc_num.setStyleSheet("color: #C62828; font-size: 18px; font-weight: 800; background: transparent;")
        lbl_inc_tag = QLabel("Incorrect")
        lbl_inc_tag.setStyleSheet("color: #C62828; font-size: 11.5px; font-weight: 600; background: transparent;")
        inc_card.layout().addWidget(self.lbl_stat_inc_num)
        inc_card.layout().addWidget(lbl_inc_tag)
        score_strip.addWidget(inc_card, 1)

        # Card 4: Time taken
        time_card = self._make_stat_card("🕒", "#1A1C1A", "#FFFDF8", "#EDD89A")
        self.lbl_stat_time = QLabel("05:24")
        self.lbl_stat_time.setStyleSheet("color: #1A1C1A; font-size: 16px; font-weight: 800; background: transparent;")
        lbl_t_sub = QLabel("Time taken")
        lbl_t_sub.setStyleSheet("color: #7A7465; font-size: 11.5px; background: transparent;")
        time_card.layout().addWidget(self.lbl_stat_time)
        time_card.layout().addWidget(lbl_t_sub)
        score_strip.addWidget(time_card, 1)

        # Card 5: Difficulty
        diff_card = self._make_stat_card("📊", "#1A1C1A", "#FFFDF8", "#EDD89A")
        self.lbl_stat_diff = QLabel("Medium")
        self.lbl_stat_diff.setStyleSheet("color: #1A1C1A; font-size: 15px; font-weight: 800; background: transparent;")
        lbl_d_sub = QLabel("Difficulty")
        lbl_d_sub.setStyleSheet("color: #7A7465; font-size: 11.5px; background: transparent;")
        diff_card.layout().addWidget(self.lbl_stat_diff)
        diff_card.layout().addWidget(lbl_d_sub)
        score_strip.addWidget(diff_card, 1)

        left_panel.addLayout(score_strip)

        # Question Review Header & Filter Chips
        rev_head = QHBoxLayout()
        lbl_qr = QLabel("Question Review")
        lbl_qr.setStyleSheet("color: #1A1C1A; font-size: 15px; font-weight: 700; background: transparent;")
        rev_head.addWidget(lbl_qr)
        rev_head.addStretch(1)

        self.btn_f_all = QPushButton("All Questions (10)")
        self.btn_f_all.setCursor(Qt.PointingHandCursor)
        self.btn_f_all.setStyleSheet("background-color: #FFD04D; border-radius: 8px; color: #1A1C1A; font-size: 11.5px; font-weight: 700; padding: 5px 10px; border: none;")
        self.btn_f_all.clicked.connect(lambda: self._set_filter("all"))

        self.btn_f_cor = QPushButton("✓ Correct (8)")
        self.btn_f_cor.setCursor(Qt.PointingHandCursor)
        self.btn_f_cor.setStyleSheet("background-color: #FCF6EC; border: 1px solid #E8DCB8; border-radius: 8px; color: #2E7D32; font-size: 11.5px; font-weight: 600; padding: 5px 10px;")
        self.btn_f_cor.clicked.connect(lambda: self._set_filter("correct"))

        self.btn_f_inc = QPushButton("✕ Incorrect (2)")
        self.btn_f_inc.setCursor(Qt.PointingHandCursor)
        self.btn_f_inc.setStyleSheet("background-color: #FCF6EC; border: 1px solid #E8DCB8; border-radius: 8px; color: #C62828; font-size: 11.5px; font-weight: 600; padding: 5px 10px;")
        self.btn_f_inc.clicked.connect(lambda: self._set_filter("incorrect"))

        rev_head.addWidget(self.btn_f_all)
        rev_head.addWidget(self.btn_f_cor)
        rev_head.addWidget(self.btn_f_inc)
        left_panel.addLayout(rev_head)

        # Scrollable Review List
        rev_scroll = QScrollArea()
        rev_scroll.setWidgetResizable(True)
        rev_scroll.setFrameShape(QFrame.NoFrame)
        rev_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        rev_scroll.setStyleSheet("QScrollArea{background: transparent; border: none;}")

        self.rev_container = QWidget()
        self.rev_container.setStyleSheet("background: transparent;")
        self.rev_lay = QVBoxLayout(self.rev_container)
        self.rev_lay.setContentsMargins(0, 0, 4, 0)
        self.rev_lay.setSpacing(12)

        rev_scroll.setWidget(self.rev_container)
        left_panel.addWidget(rev_scroll, 1)

        root.addLayout(left_panel, 62)

        # ── Right: Performance Summary, Topics, Recommendations ───────────────
        right_panel = QFrame()
        right_panel.setStyleSheet("background-color: #FFFDF8; border: 1px solid #EDD89A; border-radius: 16px;")
        rp_lay = QVBoxLayout(right_panel)
        rp_lay.setContentsMargins(18, 16, 18, 16)
        rp_lay.setSpacing(14)

        # Performance Summary Card
        ps_head = QHBoxLayout()
        ps_head.addWidget(QLabel("📊"))
        lbl_ps_title = QLabel("Performance Summary")
        lbl_ps_title.setStyleSheet("color: #1A1C1A; font-size: 14px; font-weight: 700; background: transparent;")
        ps_head.addWidget(lbl_ps_title)
        ps_head.addStretch(1)
        rp_lay.addLayout(ps_head)

        self.lbl_rp_score = QLabel("8 / 10 (80%)")
        self.lbl_rp_cor = QLabel("8")
        self.lbl_rp_inc = QLabel("2")
        self.lbl_rp_time = QLabel("05:24")
        self.lbl_rp_avg = QLabel("32 seconds")
        self.lbl_rp_diff = QLabel("Medium")
        self.lbl_rp_type = QLabel("Multiple choice (MCQ)")

        rp_lay.addLayout(self._make_sum_row("🏆", "Score", self.lbl_rp_score))
        rp_lay.addLayout(self._make_sum_row("✓", "Correct answers", self.lbl_rp_cor))
        rp_lay.addLayout(self._make_sum_row("✕", "Incorrect answers", self.lbl_rp_inc))
        rp_lay.addLayout(self._make_sum_row("🕒", "Time taken", self.lbl_rp_time))
        rp_lay.addLayout(self._make_sum_row("⏱", "Average time per question", self.lbl_rp_avg))
        rp_lay.addLayout(self._make_sum_row("📊", "Difficulty level", self.lbl_rp_diff))
        rp_lay.addLayout(self._make_sum_row("❓", "Question type", self.lbl_rp_type))

        # Topic Performance
        tp_head = QHBoxLayout()
        tp_head.addWidget(QLabel("🥧"))
        lbl_tp_t = QLabel("Topic Performance")
        lbl_tp_t.setStyleSheet("color: #1A1C1A; font-size: 13.5px; font-weight: 700; background: transparent;")
        tp_head.addWidget(lbl_tp_t)
        tp_head.addStretch(1)
        rp_lay.addLayout(tp_head)

        topics = [
            ("Introduction", 2, 2, "#2E7D32"),
            ("Data Models", 2, 3, "#2E7D32"),
            ("Database Design", 1, 2, "#F57C00"),
            ("Query Processing", 2, 2, "#2E7D32"),
            ("Transaction Management", 1, 2, "#D32F2F")
        ]
        for t_name, cur_val, max_val, bar_color in topics:
            t_row = QHBoxLayout()
            t_row.setSpacing(6)
            lbl_tn = QLabel(t_name)
            lbl_tn.setStyleSheet("color: #4A4538; font-size: 11.5px; background: transparent;")

            bar = QProgressBar()
            bar.setFixedHeight(6)
            bar.setRange(0, max_val)
            bar.setValue(cur_val)
            bar.setTextVisible(False)
            bar.setStyleSheet(
                f"QProgressBar{{background-color: #E8DCB8; border-radius: 3px; border: none;}}"
                f"QProgressBar::chunk{{background-color: {bar_color}; border-radius: 3px;}}"
            )

            lbl_tv = QLabel(f"{cur_val} / {max_val}")
            lbl_tv.setStyleSheet("color: #7A7465; font-size: 11px; background: transparent;")

            t_row.addWidget(lbl_tn, 2)
            t_row.addWidget(bar, 3)
            t_row.addWidget(lbl_tv, 1)
            rp_lay.addLayout(t_row)

        # Recommendations Card
        rec_c = QFrame()
        rec_c.setStyleSheet("background-color: #FEF9E7; border: 1px solid #F5E5B8; border-radius: 12px;")
        rc_lay = QVBoxLayout(rec_c)
        rc_lay.setContentsMargins(12, 10, 12, 10)
        rc_lay.setSpacing(6)
        rh = QHBoxLayout()
        rh.addWidget(QLabel("💡"))
        rh.addWidget(QLabel("Recommendations"))
        rh.addStretch(1)
        rc_lay.addLayout(rh)

        recs = [
            "Review the incorrect answers and read the explanations.",
            "Focus more on Database Design and Transaction Management.",
            "Try another quiz with more questions.",
            "Read the related pages in your document for better understanding."
        ]
        for r_text in recs:
            rr = QHBoxLayout()
            rr.setSpacing(6)
            chk = QLabel("✓")
            chk.setFixedSize(16, 16)
            chk.setAlignment(Qt.AlignCenter)
            chk.setStyleSheet("background-color: #FFD04D; color: #1A1C1A; font-size: 10px; font-weight: bold; border-radius: 8px;")
            lbl = QLabel(r_text)
            lbl.setWordWrap(True)
            lbl.setStyleSheet("color: #5A5445; font-size: 11px; background: transparent;")
            rr.addWidget(chk, 0, Qt.AlignTop)
            rr.addWidget(lbl, 1)
            rc_lay.addLayout(rr)
        rp_lay.addWidget(rec_c)

        rp_lay.addStretch(1)
        root.addWidget(right_panel, 38)

    def _make_stat_card(self, icon: str, text_color: str, bg_color: str, border_color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"background-color: {bg_color}; border: 1px solid {border_color}; border-radius: 12px;")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(2)
        ico = QLabel(icon)
        ico.setStyleSheet(f"color: {text_color}; font-size: 14px; font-weight: bold; background: transparent;")
        lay.addWidget(ico)
        return card

    def _make_sum_row(self, icon: str, title: str, value_lbl: QLabel) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(6)
        ico = QLabel(icon)
        ico.setStyleSheet("font-size: 12px; background: transparent;")
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("color: #5A5445; font-size: 12px; background: transparent;")
        value_lbl.setStyleSheet("color: #1A1C1A; font-size: 12px; font-weight: 600; background: transparent;")
        row.addWidget(ico)
        row.addWidget(t_lbl)
        row.addStretch(1)
        row.addWidget(value_lbl)
        return row

    def show_results(self, questions: list[dict], answers: dict, doc_name: str = ""):
        self._questions = questions or DEFAULT_DBMS_QUESTIONS
        self._answers = answers
        if doc_name:
            self._doc_name = doc_name

        total = len(self._questions)
        correct = sum(1 for i, q in enumerate(self._questions) if self._answers.get(i) == q["correct"])
        incorrect = total - correct
        pct = int(correct / total * 100) if total else 0

        self.gauge.setValue(pct)
        self.lbl_score_ratio.setText(f"{correct} / {total}")
        self.lbl_stat_c_num.setText(str(correct))
        self.lbl_stat_inc_num.setText(str(incorrect))
        self.lbl_rp_score.setText(f"{correct} / {total} ({pct}%)")
        self.lbl_rp_cor.setText(str(correct))
        self.lbl_rp_inc.setText(str(incorrect))

        self.btn_f_all.setText(f"All Questions ({total})")
        self.btn_f_cor.setText(f"✓ Correct ({correct})")
        self.btn_f_inc.setText(f"✕ Incorrect ({incorrect})")

        self._render_review_cards()

    def _set_filter(self, mode: str):
        self._filter_mode = mode
        self.btn_f_all.setStyleSheet("background-color: #FFD04D; border-radius: 8px; color: #1A1C1A; font-size: 11.5px; font-weight: 700; padding: 5px 10px; border: none;" if mode == "all" else "background-color: #FCF6EC; border: 1px solid #E8DCB8; border-radius: 8px; color: #5A5445; font-size: 11.5px; padding: 5px 10px;")
        self.btn_f_cor.setStyleSheet("background-color: #FFD04D; border-radius: 8px; color: #1A1C1A; font-size: 11.5px; font-weight: 700; padding: 5px 10px; border: none;" if mode == "correct" else "background-color: #FCF6EC; border: 1px solid #E8DCB8; border-radius: 8px; color: #2E7D32; font-size: 11.5px; padding: 5px 10px;")
        self.btn_f_inc.setStyleSheet("background-color: #FFD04D; border-radius: 8px; color: #1A1C1A; font-size: 11.5px; font-weight: 700; padding: 5px 10px; border: none;" if mode == "incorrect" else "background-color: #FCF6EC; border: 1px solid #E8DCB8; border-radius: 8px; color: #C62828; font-size: 11.5px; padding: 5px 10px;")
        self._render_review_cards()

    def _render_review_cards(self):
        _clear_layout(self.rev_lay)

        for i, q in enumerate(self._questions):
            chosen = self._answers.get(i, "—")
            correct = q["correct"]
            is_ok = (chosen == correct)

            if self._filter_mode == "correct" and not is_ok:
                continue
            if self._filter_mode == "incorrect" and is_ok:
                continue

            card = QFrame()
            card.setStyleSheet("background-color: #FFFDF8; border: 1px solid #EDD89A; border-radius: 14px;")
            c_lay = QVBoxLayout(card)
            c_lay.setContentsMargins(16, 12, 16, 12)
            c_lay.setSpacing(8)

            # Header
            head = QHBoxLayout()
            lbl_q_title = QLabel(f"{i + 1}. {q['question']}")
            lbl_q_title.setWordWrap(True)
            lbl_q_title.setStyleSheet("color: #1A1C1A; font-size: 13.5px; font-weight: 700; background: transparent;")

            status_pill = QLabel("✓ Correct" if is_ok else "✕ Incorrect")
            status_pill.setStyleSheet(
                f"background-color: {'#EDF7EE' if is_ok else '#FFEBEE'}; "
                f"color: {'#2E7D32' if is_ok else '#C62828'}; "
                f"border: 1px solid {'#C8E6C9' if is_ok else '#FFCDD2'}; "
                "border-radius: 6px; padding: 2px 8px; font-size: 11px; font-weight: bold;"
            )

            btn_pg = QPushButton(f"📖 Page {q.get('page', i + 1)}")
            btn_pg.setCursor(Qt.PointingHandCursor)
            btn_pg.setStyleSheet(
                "QPushButton{background-color: #F6ECCF; border-radius: 6px; color: #5A5445;"
                "font-size: 11px; font-weight: 600; padding: 3px 8px; border: none;}"
                "QPushButton:hover{background-color: #EEDBBA; color: #1A1C1A;}"
            )
            btn_pg.clicked.connect(lambda _, p=q.get('page', i + 1): self.openPageRequested.emit(self._doc_name, p))

            head.addWidget(lbl_q_title, 1)
            head.addWidget(status_pill)
            head.addWidget(btn_pg)
            c_lay.addLayout(head)

            # Your Answer row
            ans_row = QHBoxLayout()
            ans_row.setSpacing(8)
            badge_u = QLabel(chosen)
            badge_u.setFixedSize(20, 20)
            badge_u.setAlignment(Qt.AlignCenter)
            badge_u.setStyleSheet(
                f"background-color: {'#2E7D32' if is_ok else '#C62828'}; color: #FFFFFF;"
                "border-radius: 10px; font-size: 10.5px; font-weight: bold;"
            )
            user_opt_text = q["options"].get(chosen, "No answer selected")
            lbl_u_ans = QLabel(f"Your answer: {user_opt_text}")
            lbl_u_ans.setWordWrap(True)
            lbl_u_ans.setStyleSheet("color: #4A4538; font-size: 12px; background: transparent;")
            ans_row.addWidget(badge_u)
            ans_row.addWidget(lbl_u_ans, 1)
            c_lay.addLayout(ans_row)

            # Correct Answer row (if wrong)
            if not is_ok:
                cor_row = QHBoxLayout()
                cor_row.setSpacing(8)
                badge_c = QLabel(correct)
                badge_c.setFixedSize(20, 20)
                badge_c.setAlignment(Qt.AlignCenter)
                badge_c.setStyleSheet("background-color: #2E7D32; color: #FFFFFF; border-radius: 10px; font-size: 10.5px; font-weight: bold;")
                cor_opt_text = q["options"].get(correct, "")
                lbl_c_ans = QLabel(f"Correct answer: {cor_opt_text}")
                lbl_c_ans.setWordWrap(True)
                lbl_c_ans.setStyleSheet("color: #2E7D32; font-size: 12px; font-weight: 600; background: transparent;")
                cor_row.addWidget(badge_c)
                cor_row.addWidget(lbl_c_ans, 1)
                c_lay.addLayout(cor_row)

            # Explanation Box with AI Explanation trigger button
            exp_box = QFrame()
            exp_box.setStyleSheet("background-color: #FCF6EC; border-radius: 8px; padding: 6px 10px;")
            eb_lay = QHBoxLayout(exp_box)
            eb_lay.setContentsMargins(8, 6, 8, 6)
            eb_lay.setSpacing(8)

            lbl_e_ico = QLabel("💡")
            lbl_e_ico.setStyleSheet("font-size: 14px; background: transparent;")
            exp_txt = QLabel(f"Explanation: {q.get('explanation', '')}")
            exp_txt.setWordWrap(True)
            exp_txt.setStyleSheet("color: #5A5445; font-size: 11.5px; line-height: 1.3; background: transparent;")

            btn_ai_exp = QPushButton("🤖 Explain with AI")
            btn_ai_exp.setCursor(Qt.PointingHandCursor)
            btn_ai_exp.setStyleSheet(
                "QPushButton{background-color: #FFD04D; border-radius: 6px; color: #1A1C1A;"
                "font-size: 11px; font-weight: 700; padding: 4px 10px; border: none;}"
                "QPushButton:hover{background-color: #E8B93A;}"
            )
            btn_ai_exp.clicked.connect(lambda _, idx=i: self._open_ai_explanation(idx))

            eb_lay.addWidget(lbl_e_ico, 0, Qt.AlignTop)
            eb_lay.addWidget(exp_txt, 1)
            eb_lay.addWidget(btn_ai_exp, 0, Qt.AlignVCenter)
            c_lay.addWidget(exp_box)

            self.rev_lay.addWidget(card)

        self.rev_lay.addStretch(1)

    def _open_ai_explanation(self, index: int):
        q = self._questions[index]
        chosen = self._answers.get(index, "—")
        correct = q["correct"]

        options_list = []
        for key in ["A", "B", "C", "D"]:
            opt_text = q["options"].get(key, "")
            is_c = (key == correct)
            is_u = (key == chosen)
            options_list.append((key, opt_text, is_c, is_u))

        dlg = AIExplanationDialog(self.window())
        dlg.set_quiz_context(
            q_num=index + 1,
            total_q=len(self._questions),
            question=q["question"],
            options=options_list,
            correct_answer=f"{correct}. {q['options'].get(correct, '')}",
            user_answer=f"{chosen}. {q['options'].get(chosen, 'No answer')}",
            explanation=q.get("explanation", ""),
            doc_name=self._doc_name,
            page=q.get("page", index + 1)
        )
        dlg.openPageRequested.connect(self.openPageRequested.emit)
        dlg.followUpRequested.connect(self._on_followup_requested)
        dlg.exec()

    def _on_followup_requested(self, q_text: str, prompt_q: str, correct_ans: str, doc_name: str, page: int):
        fu_dlg = AIFollowUpDialog(self.window())
        fu_dlg.set_context(q_text, correct_ans, doc_name, page)
        fu_dlg.openPageRequested.connect(self.openPageRequested.emit)
        fu_dlg.send_user_message(prompt_q)
        fu_dlg.exec()


# ── Main QuizView Container ────────────────────────────────────────────────────

class QuizView(QWidget):
    """
    Main Quiz orchestrator hosting 4 stacked views:
    0: Config form
    1: Generation loading
    2: Question view
    3: Results view
    """

    openPageRequested = Signal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._model: str = ""
        self._doc = None
        self._doc_name: str = "Database Systems - Chapter 1.pdf"
        self._total_pages: int = 20
        self._current_page: int = 1
        self._questions: list[dict] = []
        self._worker: QuizWorker | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._stack = QStackedWidget()

        self.config_form = QuizConfigForm()
        self.loading_screen = QuizLoadingScreen()
        self.question_view = QuizQuestionView()
        self.results_view = QuizResultsView()

        self._stack.addWidget(self.config_form)     # 0
        self._stack.addWidget(self.loading_screen)  # 1
        self._stack.addWidget(self.question_view)   # 2
        self._stack.addWidget(self.results_view)    # 3

        root.addWidget(self._stack)

        self.config_form.generateRequested.connect(self._on_generate)
        self.loading_screen.cancelled.connect(self._on_cancel_generation)
        self.question_view.submitRequested.connect(self._on_submit)
        self.question_view.changeSettingsRequested.connect(self._on_retry)
        self.results_view.retryRequested.connect(self._on_retry)
        self.results_view.backToDocRequested.connect(self._on_back_to_doc)
        self.results_view.openPageRequested.connect(self.openPageRequested.emit)

    def set_context(self, model: str, doc=None, doc_name: str = "",
                    total_pages: int = 0, current_page: int = 1):
        self._model = model
        self._doc = doc
        if doc_name:
            self._doc_name = doc_name
        if total_pages:
            self._total_pages = total_pages
        if current_page:
            self._current_page = current_page

        self.config_form.update_page_info(self._current_page, self._total_pages, self._doc_name)

    def reset(self):
        self._stack.setCurrentIndex(0)

    def _on_generate(self, config: dict):
        self._stack.setCurrentIndex(1)
        self.loading_screen.start()

        # Extract text if document is available
        doc_text = ""
        if self._doc is not None:
            p_from, p_to = config.get("page_range", (1, self._total_pages))
            p_from = max(1, p_from)
            p_to = min(p_to, self._doc.page_count)
            page_texts = []
            for p in range(p_from - 1, p_to):
                blocks = pdf_service.get_text_blocks(self._doc, p)
                page_texts.append("\n".join(b["text"] for b in blocks))
            doc_text = "\n\n".join(page_texts).strip()

        # If model is configured and text is available, run worker; otherwise use high-fidelity default questions
        if self._model and doc_text:
            self._worker = QuizWorker(
                self._model, doc_text,
                config["num_questions"],
                config["difficulty"],
                config["focus"],
                parent=self
            )
            self._worker.resultReady.connect(self._on_questions_ready)
            self._worker.errorOccurred.connect(self._on_worker_error)
            self._worker.start()
        else:
            # High-fidelity simulation for offline / testing
            n = config.get("num_questions", 10)
            sim_questions = DEFAULT_DBMS_QUESTIONS[:n]
            QTimer.singleShot(1200, lambda: self._on_questions_ready(sim_questions))

    def _on_questions_ready(self, questions: list[dict]):
        self.loading_screen.stop()
        self._questions = questions or DEFAULT_DBMS_QUESTIONS
        self.question_view.load_questions(self._questions)
        self._stack.setCurrentIndex(2)

    def _on_worker_error(self, err: str):
        self.loading_screen.stop()
        self._questions = DEFAULT_DBMS_QUESTIONS
        self.question_view.load_questions(self._questions)
        self._stack.setCurrentIndex(2)

    def _on_cancel_generation(self):
        self.loading_screen.stop()
        self._stack.setCurrentIndex(0)

    def _on_submit(self, answers: dict):
        self.results_view.show_results(self._questions, answers, self._doc_name)
        self._stack.setCurrentIndex(3)

    def _on_retry(self):
        self._stack.setCurrentIndex(0)

    def _on_back_to_doc(self):
        self.openPageRequested.emit(self._doc_name, 1)
