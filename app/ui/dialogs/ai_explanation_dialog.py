"""AI Explanation Dialog — study explanation modal for reading passages and quiz questions."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor


def _clear_layout(layout):
    """Safely and recursively remove and delete all widgets and sublayouts."""
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            w = item.widget()
            w.setParent(None)
            w.deleteLater()
        elif item.layout():
            _clear_layout(item.layout())


class AIExplanationDialog(QDialog):
    """
    Detailed study explanation modal matching 'AI Explanation Study Results Dashboard.png'.
    Shared between PDF/Notes reading and Quiz question reviews.
    """

    openPageRequested   = Signal(str, int)  # (doc_name, page)
    followUpRequested   = Signal(str, str, str, str, int) # (question_text, prompt_question, correct_answer, doc_name, page)
    navigateQuestion    = Signal(int)       # -1 for prev, +1 for next

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.resize(920, 640)

        self._doc_name: str = "Database Systems - Chapter 1.pdf"
        self._page_num: int = 5
        self._current_q_index: int = 1
        self._total_questions: int = 10
        self._question_text: str = "Which component stores data physically?"
        self._correct_answer: str = "C. Storage Manager"

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)

        # Card container with drop shadow & rounded corners
        self.card = QWidget()
        self.card.setObjectName("explanationCard")
        self.card.setAttribute(Qt.WA_StyledBackground, True)
        self.card.setStyleSheet(
            "#explanationCard{"
            "background-color: #FFFDF8; border: 1px solid #EDD89A; border-radius: 20px;"
            "}"
        )
        card_lay = QVBoxLayout(self.card)
        card_lay.setContentsMargins(28, 22, 28, 22)
        card_lay.setSpacing(16)

        # ── Header ─────────────────────────────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(14)

        icon_box = QFrame()
        icon_box.setFixedSize(44, 44)
        icon_box.setStyleSheet("background-color: #FFD04D; border-radius: 12px;")
        ib_lay = QVBoxLayout(icon_box)
        ib_lay.setContentsMargins(0, 0, 0, 0)
        ib_lay.setAlignment(Qt.AlignCenter)
        ib_lbl = QLabel("💡")
        ib_lbl.setAlignment(Qt.AlignCenter)
        ib_lbl.setStyleSheet("font-size: 22px; background: transparent;")
        ib_lay.addWidget(ib_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title_lbl = QLabel("AI Explanation")
        title_lbl.setStyleSheet(
            "color: #1A1C1A; font-size: 20px; font-weight: 800; font-family: 'Segoe UI', sans-serif;"
        )
        subtitle_lbl = QLabel("Get a detailed explanation for this question powered by Ollama.")
        subtitle_lbl.setStyleSheet("color: #7A7465; font-size: 13px; font-weight: 400;")
        title_col.addWidget(title_lbl)
        title_col.addWidget(subtitle_lbl)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(30, 30)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet(
            "QPushButton{background-color: #F6ECCF; border-radius: 15px; color: #5A5445;"
            "font-size: 13px; font-weight: 700; border: none;}"
            "QPushButton:hover{background-color: #EEDBBA; color: #1A1C1A;}"
        )
        btn_close.clicked.connect(self.close)

        header.addWidget(icon_box)
        header.addLayout(title_col, 1)
        header.addWidget(btn_close)
        card_lay.addLayout(header)

        # ── Two-Column Body ────────────────────────────────────────────────────
        body = QHBoxLayout()
        body.setSpacing(20)

        # ── Left Column: Question, Options, Result Pill, Detailed Explanation ──
        left_col = QVBoxLayout()
        left_col.setSpacing(12)

        # Question Navigation & Header
        q_nav_row = QHBoxLayout()
        self.lbl_q_counter = QLabel("Question 2 of 10")
        self.lbl_q_counter.setStyleSheet("color: #5A5445; font-size: 13px; font-weight: 600;")
        q_nav_row.addWidget(self.lbl_q_counter)
        q_nav_row.addStretch(1)

        self.btn_prev_q = QPushButton("‹")
        self.btn_prev_q.setFixedSize(28, 28)
        self.btn_prev_q.setCursor(Qt.PointingHandCursor)
        self.btn_prev_q.setStyleSheet(
            "QPushButton{background-color: #FCF6EC; border: 1px solid #E8DCB8; border-radius: 8px;"
            "font-size: 16px; font-weight: bold; color: #5A5445; padding-bottom: 2px;}"
            "QPushButton:hover{background-color: #F7E7B5; color: #1A1C1A;}"
        )
        self.btn_prev_q.clicked.connect(lambda: self.navigateQuestion.emit(-1))

        self.btn_next_q = QPushButton("›")
        self.btn_next_q.setFixedSize(28, 28)
        self.btn_next_q.setCursor(Qt.PointingHandCursor)
        self.btn_next_q.setStyleSheet(
            "QPushButton{background-color: #FCF6EC; border: 1px solid #E8DCB8; border-radius: 8px;"
            "font-size: 16px; font-weight: bold; color: #5A5445; padding-bottom: 2px;}"
            "QPushButton:hover{background-color: #F7E7B5; color: #1A1C1A;}"
        )
        self.btn_next_q.clicked.connect(lambda: self.navigateQuestion.emit(1))

        q_nav_row.addWidget(self.btn_prev_q)
        q_nav_row.addWidget(self.btn_next_q)
        left_col.addLayout(q_nav_row)

        # Question Title
        self.lbl_question_title = QLabel("Which component stores data physically?")
        self.lbl_question_title.setWordWrap(True)
        self.lbl_question_title.setStyleSheet("color: #1A1C1A; font-size: 15px; font-weight: 700;")
        left_col.addWidget(self.lbl_question_title)

        # Options Container (A, B, C, D)
        self.options_container = QVBoxLayout()
        self.options_container.setSpacing(6)
        left_col.addLayout(self.options_container)

        # Answer Outcome Banner (Correct Answer / Your Answer)
        self.outcome_banner = QFrame()
        self.outcome_banner.setStyleSheet(
            "background-color: #EDF7EE; border: 1px solid #C8E6C9; border-radius: 12px; padding: 10px 14px;"
        )
        banner_lay = QHBoxLayout(self.outcome_banner)
        banner_lay.setContentsMargins(12, 8, 12, 8)
        banner_lay.setSpacing(10)

        self.outcome_icon = QLabel("✓")
        self.outcome_icon.setFixedSize(24, 24)
        self.outcome_icon.setAlignment(Qt.AlignCenter)
        self.outcome_icon.setStyleSheet(
            "background-color: #2E7D32; color: #FFFFFF; border-radius: 12px; font-size: 13px; font-weight: bold;"
        )

        outcome_text_col = QVBoxLayout()
        outcome_text_col.setSpacing(2)
        self.lbl_correct_ans = QLabel("Correct Answer: C. Storage Manager")
        self.lbl_correct_ans.setStyleSheet("color: #2E7D32; font-size: 13px; font-weight: 700; background: transparent;")
        self.lbl_user_ans = QLabel("Your answer: C. Storage Manager")
        self.lbl_user_ans.setStyleSheet("color: #5A5445; font-size: 12px; background: transparent;")
        outcome_text_col.addWidget(self.lbl_correct_ans)
        outcome_text_col.addWidget(self.lbl_user_ans)

        banner_lay.addWidget(self.outcome_icon)
        banner_lay.addLayout(outcome_text_col, 1)
        left_col.addWidget(self.outcome_banner)

        # Detailed Explanation Scroll Area
        exp_box = QFrame()
        exp_box.setStyleSheet("background-color: #FCF6EC; border-radius: 14px; border: 1px solid #E8DCB8;")
        exp_lay = QVBoxLayout(exp_box)
        exp_lay.setContentsMargins(16, 12, 16, 12)
        exp_lay.setSpacing(8)

        exp_header = QHBoxLayout()
        exp_icon = QLabel("💡")
        exp_icon.setStyleSheet("font-size: 16px; background: transparent;")
        exp_title = QLabel("Detailed Explanation")
        exp_title.setStyleSheet("color: #1A1C1A; font-size: 14px; font-weight: 700; background: transparent;")
        exp_header.addWidget(exp_icon)
        exp_header.addWidget(exp_title)
        exp_header.addStretch(1)
        exp_lay.addLayout(exp_header)

        scroll_exp = QScrollArea()
        scroll_exp.setWidgetResizable(True)
        scroll_exp.setFrameShape(QFrame.NoFrame)
        scroll_exp.setStyleSheet("QScrollArea{background: transparent; border: none;}")

        self.explanation_lbl = QLabel(
            "The Storage Manager is the component in a DBMS that is responsible for storing, "
            "retrieving, and managing data on disk. It handles the physical storage of data, "
            "including file organization, index structures, buffer management, and disk space management.\n\n"
            "The Query Processor is responsible for parsing and optimizing queries. "
            "The Transaction Manager handles concurrency control and ensures data consistency. "
            "The Authorization Manager manages user permissions and access control."
        )
        self.explanation_lbl.setWordWrap(True)
        self.explanation_lbl.setStyleSheet(
            "color: #4A4538; font-size: 12.5px; line-height: 1.5; background: transparent;"
        )
        scroll_exp.setWidget(self.explanation_lbl)
        exp_lay.addWidget(scroll_exp, 1)

        left_col.addWidget(exp_box, 1)
        body.addLayout(left_col, 58)

        # ── Right Column: Source Ref + Key Points + Follow-ups ────────────────
        right_col = QVBoxLayout()
        right_col.setSpacing(12)

        # Source Reference Card
        ref_card = QFrame()
        ref_card.setStyleSheet("background-color: #FCF6EC; border-radius: 14px; border: 1px solid #E8DCB8;")
        rf_lay = QVBoxLayout(ref_card)
        rf_lay.setContentsMargins(16, 12, 16, 12)
        rf_lay.setSpacing(8)

        rf_head = QHBoxLayout()
        rf_icon = QLabel("📄")
        rf_icon.setStyleSheet("font-size: 15px; background: transparent;")
        rf_title = QLabel("Source Reference")
        rf_title.setStyleSheet("color: #1A1C1A; font-size: 13.5px; font-weight: 700; background: transparent;")
        rf_head.addWidget(rf_icon)
        rf_head.addWidget(rf_title)
        rf_head.addStretch(1)
        rf_lay.addLayout(rf_head)

        self.source_doc_lbl = QLabel("Database Systems - Chapter 1.pdf")
        self.source_doc_lbl.setStyleSheet("color: #1A1C1A; font-size: 13px; font-weight: 600; background: transparent;")
        self.source_page_lbl = QLabel("Page 5")
        self.source_page_lbl.setStyleSheet("color: #7A7465; font-size: 12px; background: transparent;")

        rf_lay.addWidget(self.source_doc_lbl)
        rf_lay.addWidget(self.source_page_lbl)

        self.btn_open_page = QPushButton("📖  Open Page")
        self.btn_open_page.setCursor(Qt.PointingHandCursor)
        self.btn_open_page.setStyleSheet(
            "QPushButton{background-color: #FFD04D; border-radius: 9px; color: #1A1C1A;"
            "font-size: 12.5px; font-weight: 700; padding: 8px 14px; border: none;}"
            "QPushButton:hover{background-color: #E8B93A;}"
        )
        self.btn_open_page.clicked.connect(self._on_open_page)
        rf_lay.addWidget(self.btn_open_page)
        right_col.addWidget(ref_card)

        # Key Points Card
        kp_card = QFrame()
        kp_card.setStyleSheet("background-color: #FCF6EC; border-radius: 14px; border: 1px solid #E8DCB8;")
        kp_lay = QVBoxLayout(kp_card)
        kp_lay.setContentsMargins(16, 12, 16, 12)
        kp_lay.setSpacing(8)

        kp_head = QHBoxLayout()
        kp_icon = QLabel("📋")
        kp_icon.setStyleSheet("font-size: 15px; background: transparent;")
        kp_title = QLabel("Key Points")
        kp_title.setStyleSheet("color: #1A1C1A; font-size: 13.5px; font-weight: 700; background: transparent;")
        kp_head.addWidget(kp_icon)
        kp_head.addWidget(kp_title)
        kp_head.addStretch(1)
        kp_lay.addLayout(kp_head)

        self.key_points_container = QVBoxLayout()
        self.key_points_container.setSpacing(6)
        kp_lay.addLayout(self.key_points_container)
        right_col.addWidget(kp_card)

        # Follow-up Questions Card
        fu_card = QFrame()
        fu_card.setStyleSheet("background-color: #FCF6EC; border-radius: 14px; border: 1px solid #E8DCB8;")
        fu_lay = QVBoxLayout(fu_card)
        fu_lay.setContentsMargins(16, 12, 16, 12)
        fu_lay.setSpacing(8)

        fu_head = QHBoxLayout()
        fu_icon = QLabel("💬")
        fu_icon.setStyleSheet("font-size: 15px; background: transparent;")
        fu_title = QLabel("Follow-up Questions")
        fu_title.setStyleSheet("color: #1A1C1A; font-size: 13.5px; font-weight: 700; background: transparent;")
        fu_head.addWidget(fu_icon)
        fu_head.addWidget(fu_title)
        fu_head.addStretch(1)
        fu_lay.addLayout(fu_head)

        self.followup_container = QVBoxLayout()
        self.followup_container.setSpacing(6)
        fu_lay.addLayout(self.followup_container)
        right_col.addWidget(fu_card)

        body.addLayout(right_col, 42)
        card_lay.addLayout(body, 1)

        outer.addWidget(self.card)

        # Set default options & content matching reference mockup
        self.set_options([
            ("A", "Query Processor", False, False),
            ("B", "Transaction Manager", False, False),
            ("C", "Storage Manager", True, True),
            ("D", "Authorization Manager", False, False),
        ])
        self.set_key_points([
            "Handles physical storage of data on disk.",
            "Manages file organization and indexes.",
            "Works with buffer management and disk space.",
            "Different from query processing and transaction management."
        ])
        self.set_followup_questions([
            "Can you give a real-world example of a storage manager?",
            "How does the storage manager handle large datasets?",
            "What is the difference between logical and physical storage?"
        ])

    def set_options(self, options: list[tuple[str, str, bool, bool]]):
        """options is list of (letter, text, is_correct, is_user_selected)"""
        _clear_layout(self.options_container)

        for letter, text, is_correct, is_selected in options:
            opt_frame = QFrame()
            if is_correct:
                opt_frame.setStyleSheet(
                    "background-color: #E8F5E9; border: 1.5px solid #81C784; border-radius: 10px;"
                )
            elif is_selected and not is_correct:
                opt_frame.setStyleSheet(
                    "background-color: #FFEBEE; border: 1.5px solid #E57373; border-radius: 10px;"
                )
            else:
                opt_frame.setStyleSheet(
                    "background-color: #FFFFFF; border: 1px solid #E8DCB8; border-radius: 10px;"
                )
            row = QHBoxLayout(opt_frame)
            row.setContentsMargins(12, 7, 12, 7)
            row.setSpacing(10)

            badge = QLabel(letter)
            badge.setFixedSize(22, 22)
            badge.setAlignment(Qt.AlignCenter)
            if is_correct:
                badge.setStyleSheet("background-color: #2E7D32; color: #FFFFFF; border-radius: 11px; font-weight: bold; font-size: 11px;")
            elif is_selected:
                badge.setStyleSheet("background-color: #C62828; color: #FFFFFF; border-radius: 11px; font-weight: bold; font-size: 11px;")
            else:
                badge.setStyleSheet("background-color: #F0EAE1; color: #5A5445; border-radius: 11px; font-weight: bold; font-size: 11px;")

            lbl_text = QLabel(text)
            lbl_text.setStyleSheet(
                f"color: {'#1B5E20' if is_correct else ('#B71C1C' if is_selected else '#1A1C1A')}; "
                f"font-size: 13px; font-weight: {'700' if is_correct else '500'}; background: transparent;"
            )
            row.addWidget(badge)
            row.addWidget(lbl_text, 1)

            if is_correct:
                chk = QLabel("✓")
                chk.setStyleSheet("color: #2E7D32; font-size: 13px; font-weight: bold; background: transparent;")
                row.addWidget(chk)

            self.options_container.addWidget(opt_frame)

    def set_key_points(self, points: list[str]):
        _clear_layout(self.key_points_container)

        for pt in points:
            row_w = QWidget()
            row = QHBoxLayout(row_w)
            row.setContentsMargins(0, 2, 0, 2)
            row.setSpacing(8)

            chk = QLabel("✓")
            chk.setFixedSize(18, 18)
            chk.setAlignment(Qt.AlignCenter)
            chk.setStyleSheet("background-color: #FFD04D; color: #1A1C1A; border-radius: 9px; font-size: 11px; font-weight: bold;")

            lbl = QLabel(pt)
            lbl.setWordWrap(True)
            lbl.setStyleSheet("color: #4A4538; font-size: 12px; line-height: 1.3; background: transparent;")

            row.addWidget(chk, 0, Qt.AlignTop)
            row.addWidget(lbl, 1)
            self.key_points_container.addWidget(row_w)

    def set_followup_questions(self, questions: list[str]):
        _clear_layout(self.followup_container)

        for q in questions:
            btn = QPushButton(f"{q}")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(
                "QPushButton{background-color: #FCF6EC; border: 1px solid #E8DCB8; border-radius: 8px; color: #1A1C1A;"
                "font-size: 11.5px; font-weight: 500; text-align: left; padding: 7px 10px;}"
                "QPushButton:hover{background-color: #F6ECCF; font-weight: 600; border-color: #EDD89A;}"
            )
            # Add chevron icon or text
            row_btn = QHBoxLayout(btn)
            row_btn.setContentsMargins(6, 0, 8, 0)
            chev = QLabel("›")
            chev.setStyleSheet("color: #9A9485; font-size: 14px; font-weight: bold; background: transparent;")
            row_btn.addStretch(1)
            row_btn.addWidget(chev)

            btn.clicked.connect(lambda _, qtext=q: self._on_followup_clicked(qtext))
            self.followup_container.addWidget(btn)

    def set_quiz_context(self, q_num: int, total_q: int, question: str, options: list[tuple[str, str, bool, bool]],
                         correct_answer: str, user_answer: str, explanation: str,
                         doc_name: str, page: int):
        self._current_q_index = q_num
        self._total_questions = total_q
        self._doc_name = doc_name
        self._page_num = page
        self._question_text = question
        self._correct_answer = correct_answer

        self.lbl_q_counter.setText(f"Question {q_num} of {total_q}")
        self.lbl_question_title.setText(question)
        self.set_options(options)

        # Outcome banner
        is_user_correct = (correct_answer.strip() == user_answer.strip()) or (user_answer in correct_answer)
        if is_user_correct:
            self.outcome_banner.setStyleSheet(
                "background-color: #EDF7EE; border: 1px solid #C8E6C9; border-radius: 12px; padding: 10px 14px;"
            )
            self.outcome_icon.setText("✓")
            self.outcome_icon.setStyleSheet(
                "background-color: #2E7D32; color: #FFFFFF; border-radius: 12px; font-size: 13px; font-weight: bold;"
            )
            self.lbl_correct_ans.setText(f"Correct Answer: {correct_answer}")
            self.lbl_correct_ans.setStyleSheet("color: #2E7D32; font-size: 13px; font-weight: 700; background: transparent;")
            self.lbl_user_ans.setText(f"Your answer: {user_answer}")
        else:
            self.outcome_banner.setStyleSheet(
                "background-color: #FBE9E7; border: 1px solid #FFCCBC; border-radius: 12px; padding: 10px 14px;"
            )
            self.outcome_icon.setText("✕")
            self.outcome_icon.setStyleSheet(
                "background-color: #C62828; color: #FFFFFF; border-radius: 12px; font-size: 13px; font-weight: bold;"
            )
            self.lbl_correct_ans.setText(f"Correct Answer: {correct_answer}")
            self.lbl_correct_ans.setStyleSheet("color: #2E7D32; font-size: 13px; font-weight: 700; background: transparent;")
            self.lbl_user_ans.setText(f"Your answer: {user_answer}")

        self.explanation_lbl.setText(explanation)
        self.source_doc_lbl.setText(doc_name)
        self.source_page_lbl.setText(f"Page {page}")

    def set_reading_context(self, selected_text: str, explanation: str, doc_name: str, page: int):
        self._doc_name = doc_name
        self._page_num = page
        self._question_text = selected_text
        self._correct_answer = ""

        self.lbl_q_counter.setText("Selected Concept")
        self.btn_prev_q.hide()
        self.btn_next_q.hide()
        self.lbl_question_title.setText(selected_text)
        _clear_layout(self.options_container)
        self.outcome_banner.hide()
        self.explanation_lbl.setText(explanation)
        self.source_doc_lbl.setText(doc_name)
        self.source_page_lbl.setText(f"Page {page}")

    def _on_open_page(self):
        self.openPageRequested.emit(self._doc_name, self._page_num)
        self.accept()

    def _on_followup_clicked(self, prompt_question: str):
        self.followUpRequested.emit(
            self._question_text,
            prompt_question,
            self._correct_answer,
            self._doc_name,
            self._page_num
        )
        self.accept()
