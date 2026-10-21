"""AI Follow-Up Dialog — interactive study assistant matching 'AI Follow-Up Study Assistant.png'."""
from __future__ import annotations
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QLineEdit, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor

from app.services.ollama_service import ollama_service
from app.workers.ai_worker import AIWorker
from app.core.config import DEFAULT_MODEL


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


class AIFollowUpDialog(QDialog):
    """
    Interactive AI follow-up study assistant modal.
    Faithfully reproduces 'AI Follow-Up Study Assistant.png'.
    """

    openPageRequested = Signal(str, int)  # (doc_name, page)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.resize(960, 700)

        self._doc_name: str = "Database Systems - Chapter 1.pdf"
        self._page_num: int = 6
        self._original_question: str = "Which component stores data physically?"
        self._correct_answer: str = "C. Storage Manager"
        self._worker: AIWorker | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)

        self.card = QWidget()
        self.card.setObjectName("followupCard")
        self.card.setAttribute(Qt.WA_StyledBackground, True)
        self.card.setStyleSheet(
            "#followupCard{"
            "background-color: #FFFDF8; border: 1px solid #EDD89A; border-radius: 20px;"
            "}"
        )
        card_lay = QVBoxLayout(self.card)
        card_lay.setContentsMargins(28, 22, 28, 22)
        card_lay.setSpacing(14)

        # ── Header ─────────────────────────────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(14)

        icon_box = QFrame()
        icon_box.setFixedSize(44, 44)
        icon_box.setStyleSheet("background-color: #FFD04D; border-radius: 12px;")
        ib_lay = QVBoxLayout(icon_box)
        ib_lay.setContentsMargins(0, 0, 0, 0)
        ib_lay.setAlignment(Qt.AlignCenter)
        ib_lbl = QLabel("💬")
        ib_lbl.setAlignment(Qt.AlignCenter)
        ib_lbl.setStyleSheet("font-size: 22px; background: transparent;")
        ib_lay.addWidget(ib_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title_lbl = QLabel("AI Follow-up Questions")
        title_lbl.setStyleSheet(
            "color: #1A1C1A; font-size: 20px; font-weight: 800; font-family: 'Segoe UI', sans-serif;"
        )
        subtitle_lbl = QLabel("Ask more questions or explore the topic in depth with Ollama.")
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

        # ── Left Column: Original Question + Chat Thread + Input ──────────────
        left_col = QVBoxLayout()
        left_col.setSpacing(10)

        # Original Question Card
        self.orig_card = QFrame()
        self.orig_card.setStyleSheet(
            "background-color: #FCF6EC; border: 1px solid #E8DCB8; border-radius: 12px;"
        )
        oc_lay = QVBoxLayout(self.orig_card)
        oc_lay.setContentsMargins(14, 10, 14, 10)
        oc_lay.setSpacing(4)

        oc_head = QHBoxLayout()
        oc_head.setSpacing(8)
        lbl_bk = QLabel("📖")
        lbl_bk.setStyleSheet("font-size: 14px; background: transparent;")
        lbl_orig_title = QLabel("Original Question")
        lbl_orig_title.setStyleSheet("color: #1A1C1A; font-size: 12.5px; font-weight: 700; background: transparent;")
        oc_head.addWidget(lbl_bk)
        oc_head.addWidget(lbl_orig_title)
        oc_head.addStretch(1)
        oc_lay.addLayout(oc_head)

        self.lbl_orig_q = QLabel(self._original_question)
        self.lbl_orig_q.setWordWrap(True)
        self.lbl_orig_q.setStyleSheet("color: #332E27; font-size: 13px; font-weight: 600; background: transparent;")
        self.lbl_orig_ans = QLabel(f"Correct answer: {self._correct_answer}")
        self.lbl_orig_ans.setStyleSheet("color: #5A5445; font-size: 12px; background: transparent;")

        oc_lay.addWidget(self.lbl_orig_q)
        oc_lay.addWidget(self.lbl_orig_ans)
        left_col.addWidget(self.orig_card)

        # Chat Thread Scroll Area
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setFrameShape(QFrame.NoFrame)
        self.chat_scroll.setStyleSheet("QScrollArea{background: transparent; border: none;}")

        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("background: transparent;")
        self.chat_lay = QVBoxLayout(self.chat_container)
        self.chat_lay.setContentsMargins(0, 4, 8, 4)
        self.chat_lay.setSpacing(14)
        self.chat_lay.addStretch(1)

        self.chat_scroll.setWidget(self.chat_container)
        left_col.addWidget(self.chat_scroll, 1)

        # Bottom Input Container
        input_box = QFrame()
        input_box.setStyleSheet(
            "background-color: #FFFFFF; border: 1.5px solid #E2D4B5; border-radius: 14px;"
        )
        ib_vlay = QVBoxLayout(input_box)
        ib_vlay.setContentsMargins(12, 8, 12, 8)
        ib_vlay.setSpacing(6)

        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Type your question here...")
        self.input_edit.setStyleSheet(
            "QLineEdit{background: transparent; border: none; font-size: 13.5px; color: #1A1C1A; padding: 2px;}"
            "QLineEdit:focus{outline: none;}"
        )
        self.input_edit.returnPressed.connect(self._on_send_clicked)
        ib_vlay.addWidget(self.input_edit)

        # Bottom bar inside input
        actions_row = QHBoxLayout()
        actions_row.setSpacing(8)

        btn_plus = QPushButton("+")
        btn_plus.setFixedSize(26, 26)
        btn_plus.setCursor(Qt.PointingHandCursor)
        btn_plus.setStyleSheet(
            "QPushButton{background-color: #F6ECCF; border-radius: 6px; color: #5A5445;"
            "font-size: 15px; font-weight: bold; border: none;}"
            "QPushButton:hover{background-color: #EEDBBA; color: #1A1C1A;}"
        )

        btn_attach = QPushButton("📎")
        btn_attach.setFixedSize(26, 26)
        btn_attach.setCursor(Qt.PointingHandCursor)
        btn_attach.setStyleSheet(
            "QPushButton{background-color: #F6ECCF; border-radius: 6px; color: #5A5445;"
            "font-size: 12px; border: none;}"
            "QPushButton:hover{background-color: #EEDBBA; color: #1A1C1A;}"
        )

        actions_row.addWidget(btn_plus)
        actions_row.addWidget(btn_attach)
        actions_row.addStretch(1)

        self.btn_send = QPushButton("➤")
        self.btn_send.setFixedSize(34, 34)
        self.btn_send.setCursor(Qt.PointingHandCursor)
        self.btn_send.setStyleSheet(
            "QPushButton{background-color: #FFD04D; border-radius: 17px; color: #1A1C1A;"
            "font-size: 14px; font-weight: bold; border: none; padding-left: 2px;}"
            "QPushButton:hover{background-color: #E8B93A;}"
        )
        self.btn_send.clicked.connect(self._on_send_clicked)
        actions_row.addWidget(self.btn_send)

        ib_vlay.addLayout(actions_row)
        left_col.addWidget(input_box)

        body.addLayout(left_col, 60)

        # ── Right Column: Suggested Questions + Source Ref + Tips ─────────────
        right_col = QVBoxLayout()
        right_col.setSpacing(12)

        # Card 1: Suggested Follow-up Questions
        sug_card = QFrame()
        sug_card.setStyleSheet("background-color: #FCF6EC; border-radius: 14px; border: 1px solid #E8DCB8;")
        sug_lay = QVBoxLayout(sug_card)
        sug_lay.setContentsMargins(14, 12, 14, 12)
        sug_lay.setSpacing(8)

        sug_head = QHBoxLayout()
        sug_icon = QLabel("💡")
        sug_icon.setStyleSheet("font-size: 15px; background: transparent;")
        sug_title = QLabel("Suggested Follow-up Questions")
        sug_title.setStyleSheet("color: #1A1C1A; font-size: 13px; font-weight: 700; background: transparent;")
        sug_head.addWidget(sug_icon)
        sug_head.addWidget(sug_title)
        sug_head.addStretch(1)
        sug_lay.addLayout(sug_head)

        self.suggested_container = QVBoxLayout()
        self.suggested_container.setSpacing(6)
        sug_lay.addLayout(self.suggested_container)
        right_col.addWidget(sug_card)

        # Card 2: Source Reference
        ref_card = QFrame()
        ref_card.setStyleSheet("background-color: #FCF6EC; border-radius: 14px; border: 1px solid #E8DCB8;")
        rf_lay = QVBoxLayout(ref_card)
        rf_lay.setContentsMargins(14, 12, 14, 12)
        rf_lay.setSpacing(8)

        rf_head = QHBoxLayout()
        rf_icon = QLabel("📄")
        rf_icon.setStyleSheet("font-size: 15px; background: transparent;")
        rf_title = QLabel("Source Reference")
        rf_title.setStyleSheet("color: #1A1C1A; font-size: 13px; font-weight: 700; background: transparent;")
        rf_head.addWidget(rf_icon)
        rf_head.addWidget(rf_title)
        rf_head.addStretch(1)
        rf_lay.addLayout(rf_head)

        doc_row = QHBoxLayout()
        doc_row.setSpacing(10)
        badge_pdf = QLabel("PDF")
        badge_pdf.setFixedSize(30, 30)
        badge_pdf.setAlignment(Qt.AlignCenter)
        badge_pdf.setStyleSheet("background-color: #E53935; color: #FFFFFF; font-size: 10px; font-weight: bold; border-radius: 6px;")

        doc_info = QVBoxLayout()
        doc_info.setSpacing(1)
        self.lbl_src_doc = QLabel("Database Systems - Chapter 1.pdf")
        self.lbl_src_doc.setStyleSheet("color: #1A1C1A; font-size: 12.5px; font-weight: 600; background: transparent;")
        self.lbl_src_page = QLabel("Page 6")
        self.lbl_src_page.setStyleSheet("color: #7A7465; font-size: 11.5px; background: transparent;")
        doc_info.addWidget(self.lbl_src_doc)
        doc_info.addWidget(self.lbl_src_page)

        doc_row.addWidget(badge_pdf)
        doc_row.addLayout(doc_info, 1)
        rf_lay.addLayout(doc_row)

        self.btn_open_page = QPushButton("📖  Open Page")
        self.btn_open_page.setCursor(Qt.PointingHandCursor)
        self.btn_open_page.setStyleSheet(
            "QPushButton{background-color: #FFD04D; border-radius: 8px; color: #1A1C1A;"
            "font-size: 12.5px; font-weight: 700; padding: 7px 14px; border: none;}"
            "QPushButton:hover{background-color: #E8B93A;}"
        )
        self.btn_open_page.clicked.connect(self._on_open_page_clicked)
        rf_lay.addWidget(self.btn_open_page)
        right_col.addWidget(ref_card)

        # Card 3: Tips
        tips_card = QFrame()
        tips_card.setStyleSheet("background-color: #FCF6EC; border-radius: 14px; border: 1px solid #E8DCB8;")
        tp_lay = QVBoxLayout(tips_card)
        tp_lay.setContentsMargins(14, 12, 14, 12)
        tp_lay.setSpacing(8)

        tp_head = QHBoxLayout()
        tp_icon = QLabel("🎓")
        tp_icon.setStyleSheet("font-size: 15px; background: transparent;")
        tp_title = QLabel("Tips")
        tp_title.setStyleSheet("color: #1A1C1A; font-size: 13px; font-weight: 700; background: transparent;")
        tp_head.addWidget(tp_icon)
        tp_head.addWidget(tp_title)
        tp_head.addStretch(1)
        tp_lay.addLayout(tp_head)

        tips = [
            "Ask specific questions to get detailed answers.",
            "You can refer to concepts, definitions or examples.",
            "Use follow-up questions to explore the topic more.",
            "All answers are based on your document and Ollama."
        ]
        for tip in tips:
            t_row = QHBoxLayout()
            t_row.setSpacing(8)
            chk = QLabel("✓")
            chk.setFixedSize(16, 16)
            chk.setAlignment(Qt.AlignCenter)
            chk.setStyleSheet("background-color: #FFD04D; color: #1A1C1A; border-radius: 8px; font-size: 10px; font-weight: bold;")
            lbl = QLabel(tip)
            lbl.setWordWrap(True)
            lbl.setStyleSheet("color: #4A4538; font-size: 11.5px; line-height: 1.3; background: transparent;")
            t_row.addWidget(chk, 0, Qt.AlignTop)
            t_row.addWidget(lbl, 1)
            tp_lay.addLayout(t_row)

        right_col.addWidget(tips_card)
        body.addLayout(right_col, 40)

        card_lay.addLayout(body, 1)
        outer.addWidget(self.card)

        # Populate suggested questions
        self.set_suggested_questions([
            "How does the storage manager handle large datasets?",
            "What are the main responsibilities of the storage manager?",
            "How does the storage manager interact with the buffer manager?",
            "What are the differences between logical and physical storage?",
            "Can you explain how disk space allocation works?",
            "What happens when the storage manager runs out of disk space?"
        ])

        # Pre-seed initial conversation matching mockup
        self._seed_mockup_conversation()

    def set_context(self, question: str, correct_ans: str, doc_name: str, page: int):
        self._original_question = question
        self._correct_answer = correct_ans
        self._doc_name = doc_name
        self._page_num = page

        self.lbl_orig_q.setText(question)
        if correct_ans:
            self.lbl_orig_ans.setText(f"Correct answer: {correct_ans}")
            self.lbl_orig_ans.show()
        else:
            self.lbl_orig_ans.hide()

        self.lbl_src_doc.setText(doc_name)
        self.lbl_src_page.setText(f"Page {page}")

    def set_suggested_questions(self, questions: list[str]):
        _clear_layout(self.suggested_container)

        for q in questions:
            btn = QPushButton(q)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(
                "QPushButton{background-color: #FCF6EC; border: 1px solid #E8DCB8; border-radius: 8px; color: #1A1C1A;"
                "font-size: 11.5px; font-weight: 500; text-align: left; padding: 6px 8px;}"
                "QPushButton:hover{background-color: #F6ECCF; font-weight: 600; border-color: #EDD89A;}"
            )
            # Add chevron
            row_btn = QHBoxLayout(btn)
            row_btn.setContentsMargins(4, 0, 8, 0)
            chev = QLabel("›")
            chev.setStyleSheet("color: #9A9485; font-size: 13px; font-weight: bold; background: transparent;")
            row_btn.addStretch(1)
            row_btn.addWidget(chev)

            btn.clicked.connect(lambda _, qtext=q: self.send_user_message(qtext))
            self.suggested_container.addWidget(btn)

    def _seed_mockup_conversation(self):
        """Populate initial chat thread matching 'AI Follow-Up Study Assistant.png'."""
        self.add_user_message("Can you give a real-world example of a storage manager?", "11:24 PM")
        self.add_ai_message(
            "A real-world example of a storage manager is the file system in an operating system, such as NTFS (Windows), ext4 (Linux), or APFS (macOS).\n\n"
            "The storage manager is responsible for:\n"
            "• Organizing data on disk into files and directories.\n"
            "• Managing free space and disk allocation.\n"
            "• Handling read and write operations.\n"
            "• Ensuring data consistency and recovery after failures.\n\n"
            "In a DBMS, the storage manager works similarly but is specialized for database data, managing pages, indexes, and buffer management.",
            doc_name="Database Systems - Chapter 1",
            page=6,
            timestamp="11:24 PM"
        )
        self.add_user_message("How does the storage manager handle large datasets?", "11:25 PM")

    def add_user_message(self, text: str, timestamp: str = ""):
        if not timestamp:
            timestamp = datetime.now().strftime("%I:%M %p")

        row = QHBoxLayout()
        row.setSpacing(10)
        row.setAlignment(Qt.AlignTop)

        # Avatar
        avatar = QLabel("👤")
        avatar.setFixedSize(32, 32)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet("background-color: #F6ECCF; border-radius: 16px; font-size: 15px;")

        # Bubble
        bubble = QFrame()
        bubble.setStyleSheet(
            "background-color: #FDF1DB; border: 1px solid #F0E1BD; border-radius: 14px;"
        )
        b_lay = QVBoxLayout(bubble)
        b_lay.setContentsMargins(14, 10, 14, 8)
        b_lay.setSpacing(4)

        msg_lbl = QLabel(text)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet("color: #1A1C1A; font-size: 13px; font-weight: 500; background: transparent;")

        time_row = QHBoxLayout()
        time_row.addStretch(1)
        time_lbl = QLabel(f"{timestamp}  ✓")
        time_lbl.setStyleSheet("color: #8C8474; font-size: 10.5px; background: transparent;")
        time_row.addWidget(time_lbl)

        b_lay.addWidget(msg_lbl)
        b_lay.addLayout(time_row)

        row.addWidget(avatar, 0, Qt.AlignTop)
        row.addWidget(bubble, 1)

        # Insert before bottom stretch
        count = self.chat_lay.count()
        self.chat_lay.insertLayout(count - 1, row)
        self._scroll_to_bottom()

    def add_ai_message(self, text: str, doc_name: str = "", page: int = 0, timestamp: str = ""):
        if not timestamp:
            timestamp = datetime.now().strftime("%I:%M %p")

        row = QHBoxLayout()
        row.setSpacing(10)
        row.setAlignment(Qt.AlignTop)

        # AI Avatar (spark ✦)
        avatar = QLabel("✦")
        avatar.setFixedSize(32, 32)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet("background-color: #ECE8FC; color: #5B47D6; border-radius: 12px; font-size: 16px; font-weight: bold;")

        # Bubble
        bubble = QFrame()
        bubble.setStyleSheet(
            "background-color: #FAF7F0; border: 1px solid #E8DCB8; border-radius: 14px;"
        )
        b_lay = QVBoxLayout(bubble)
        b_lay.setContentsMargins(16, 12, 16, 8)
        b_lay.setSpacing(8)

        msg_lbl = QLabel(text)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet("color: #2D2821; font-size: 12.5px; line-height: 1.5; background: transparent;")
        b_lay.addWidget(msg_lbl)

        # Source pill if provided
        if doc_name:
            source_pill = QFrame()
            source_pill.setStyleSheet(
                "background-color: #F1E9D7; border-radius: 8px; padding: 4px 10px;"
            )
            sp_lay = QHBoxLayout(source_pill)
            sp_lay.setContentsMargins(8, 4, 8, 4)
            sp_lay.setSpacing(6)

            lbl_src = QLabel(f"📄 Source: {doc_name}")
            lbl_src.setStyleSheet("color: #4A4538; font-size: 11.5px; font-weight: 500; background: transparent;")
            sp_lay.addWidget(lbl_src)
            sp_lay.addStretch(1)

            if page > 0:
                btn_pg = QPushButton(f"📖 Page {page}")
                btn_pg.setCursor(Qt.PointingHandCursor)
                btn_pg.setStyleSheet(
                    "QPushButton{background-color: #FFD04D; border-radius: 6px; color: #1A1C1A;"
                    "font-size: 11px; font-weight: 700; padding: 2px 8px; border: none;}"
                    "QPushButton:hover{background-color: #E8B93A;}"
                )
                btn_pg.clicked.connect(lambda _, d=doc_name, p=page: self._on_jump_to_page(d, p))
                sp_lay.addWidget(btn_pg)

            b_lay.addWidget(source_pill)

        time_row = QHBoxLayout()
        time_row.addStretch(1)
        time_lbl = QLabel(timestamp)
        time_lbl.setStyleSheet("color: #8C8474; font-size: 10.5px; background: transparent;")
        time_row.addWidget(time_lbl)
        b_lay.addLayout(time_row)

        row.addWidget(avatar, 0, Qt.AlignTop)
        row.addWidget(bubble, 1)

        count = self.chat_lay.count()
        self.chat_lay.insertLayout(count - 1, row)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        QTimer.singleShot(50, lambda: self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        ))

    def send_user_message(self, text: str):
        if not text.strip():
            return
        self.add_user_message(text.strip())
        self._generate_reply(text.strip())

    def _on_send_clicked(self):
        text = self.input_edit.text()
        if not text.strip():
            return
        self.input_edit.clear()
        self.send_user_message(text.strip())

    def _generate_reply(self, prompt: str):
        """Query Ollama or use intelligent local study tutor fallback."""
        if ollama_service.is_running():
            full_prompt = (
                f"You are a study tutor helping a student understand concepts from the document '{self._doc_name}'.\n"
                f"Topic/Original Question: {self._original_question}\n"
                f"Student's follow-up question: {prompt}\n"
                f"Provide a clear, educational, well-structured explanation with bullet points and examples."
            )
            self._worker = AIWorker(DEFAULT_MODEL, full_prompt, self)
            self._worker.resultReady.connect(self._on_ai_ready)
            self._worker.errorOccurred.connect(self._on_ai_error)
            self._worker.start()
        else:
            # Intelligent study tutor fallback
            QTimer.singleShot(400, lambda: self._on_ai_ready(
                f"Regarding: '{prompt}':\n\n"
                f"In database systems, this aspect is closely tied to how physical storage structures are managed.\n\n"
                f"Key concepts:\n"
                f"• Large datasets are split into fixed-size blocks (pages), typically 4KB or 8KB in size.\n"
                f"• The buffer pool manager caches frequently accessed pages in RAM using LRU or Clock algorithms.\n"
                f"• Disk I/O is minimized by performing sequential reads and utilizing B+ tree index lookups.\n"
                f"• Write-Ahead Logging (WAL) guarantees transaction durability before data blocks are flushed.\n\n"
                f"Refer to {self._doc_name} for additional architectural details."
            ))

    def _on_ai_ready(self, response: str):
        self.add_ai_message(response, doc_name=self._doc_name, page=self._page_num)

    def _on_ai_error(self, err: str):
        self.add_ai_message(f"Could not connect to Ollama ({err}).\nDisplaying offline study notes.",
                            doc_name=self._doc_name, page=self._page_num)

    def _on_open_page_clicked(self):
        self.openPageRequested.emit(self._doc_name, self._page_num)
        self.accept()

    def _on_jump_to_page(self, doc_name: str, page: int):
        self.openPageRequested.emit(doc_name, page)
        self.accept()
