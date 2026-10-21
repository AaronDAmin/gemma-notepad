"""Error and unsupported file dialogs matching reference mockups:
- GemmaNotepad1 Ollama Connection Error.png
- Unsupported File Type Dialog in GemmaNotepad1-2.png
"""
from __future__ import annotations
import os
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor


class OllamaConnectionErrorDialog(QDialog):
    """
    Ollama connection error modal matching 'GemmaNotepad1 Ollama Connection Error.png'.
    """

    retryRequested = Signal()
    openOllamaRequested = Signal()

    def __init__(self, host: str = "http://localhost:11434", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.resize(540, 520)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)

        card = QWidget()
        card.setObjectName("errorCard")
        card.setAttribute(Qt.WA_StyledBackground, True)
        card.setStyleSheet(
            "#errorCard{"
            "background-color: #FFFDF8; border: 1px solid #EDD89A; border-radius: 20px;"
            "}"
        )
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(28, 22, 28, 22)
        card_lay.setSpacing(14)

        # Header close button
        top_row = QHBoxLayout()
        top_row.addStretch(1)
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(28, 28)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet(
            "QPushButton{background-color: #F6ECCF; border-radius: 14px; color: #5A5445;"
            "font-size: 13px; font-weight: 700; border: none;}"
            "QPushButton:hover{background-color: #EEDBBA; color: #1A1C1A;}"
        )
        btn_close.clicked.connect(self.reject)
        top_row.addWidget(btn_close)
        card_lay.addLayout(top_row)

        # Center illustration & Title
        center_col = QVBoxLayout()
        center_col.setAlignment(Qt.AlignCenter)
        center_col.setSpacing(8)

        lbl_bot = QLabel("🤖 ❗")
        lbl_bot.setAlignment(Qt.AlignCenter)
        lbl_bot.setStyleSheet("font-size: 42px; background: transparent;")
        center_col.addWidget(lbl_bot)

        lbl_title = QLabel("Cannot Connect to Ollama")
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet("color: #1A1C1A; font-size: 20px; font-weight: 800; font-family: 'Segoe UI', sans-serif; background: transparent;")
        center_col.addWidget(lbl_title)

        lbl_sub = QLabel(f"GemmaNotepad1 is unable to connect to your local Ollama server\nat {host}.")
        lbl_sub.setAlignment(Qt.AlignCenter)
        lbl_sub.setStyleSheet("color: #7A7465; font-size: 12.5px; background: transparent;")
        center_col.addWidget(lbl_sub)
        card_lay.addLayout(center_col)

        # Red Error Card
        err_box = QFrame()
        err_box.setStyleSheet("background-color: #FDECEC; border: 1px solid #F5C6CB; border-radius: 12px;")
        eb_lay = QHBoxLayout(err_box)
        eb_lay.setContentsMargins(14, 10, 14, 10)
        eb_lay.setSpacing(10)

        err_ico = QLabel("❗")
        err_ico.setStyleSheet("font-size: 16px; background: transparent;")
        err_txt_col = QVBoxLayout()
        err_txt_col.setSpacing(2)
        lbl_e_title = QLabel("Connection Error")
        lbl_e_title.setStyleSheet("color: #721C24; font-size: 13px; font-weight: 700; background: transparent;")
        lbl_e_msg = QLabel("The application could not reach the Ollama server.\nPlease make sure Ollama is running on your computer.")
        lbl_e_msg.setStyleSheet("color: #491217; font-size: 11.5px; background: transparent;")
        err_txt_col.addWidget(lbl_e_title)
        err_txt_col.addWidget(lbl_e_msg)
        eb_lay.addWidget(err_ico, 0, Qt.AlignTop)
        eb_lay.addLayout(err_txt_col, 1)
        card_lay.addWidget(err_box)

        # Yellow Steps Card
        steps_box = QFrame()
        steps_box.setStyleSheet("background-color: #FEF9E7; border: 1px solid #F5E5B8; border-radius: 12px;")
        sb_lay = QVBoxLayout(steps_box)
        sb_lay.setContentsMargins(14, 10, 14, 10)
        sb_lay.setSpacing(6)

        sb_head = QHBoxLayout()
        sb_head.setSpacing(6)
        lbl_sb_ico = QLabel("💡")
        lbl_sb_title = QLabel("Try these steps:")
        lbl_sb_title.setStyleSheet("color: #1A1C1A; font-size: 12.5px; font-weight: 700; background: transparent;")
        sb_head.addWidget(lbl_sb_ico)
        sb_head.addWidget(lbl_sb_title)
        sb_head.addStretch(1)
        sb_lay.addLayout(sb_head)

        steps = [
            "1. Make sure Ollama is installed on your computer.",
            "2. Start the Ollama server from your terminal:  ollama serve",
            f"3. Check that the server is running at {host}.",
            "4. Verify that no firewall is blocking the connection."
        ]
        for s in steps:
            lbl_s = QLabel(s)
            lbl_s.setStyleSheet("color: #4A4538; font-size: 11.5px; background: transparent;")
            sb_lay.addWidget(lbl_s)
        card_lay.addWidget(steps_box)

        # Actions Row
        actions = QHBoxLayout()
        actions.setSpacing(10)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet(
            "QPushButton{background-color: #FFFFFF; border: 1px solid #DCD5C5; border-radius: 10px;"
            "color: #1A1C1A; font-size: 12.5px; font-weight: 600; padding: 9px 18px;}"
            "QPushButton:hover{background-color: #F8F5EE;}"
        )
        btn_cancel.clicked.connect(self.reject)

        btn_open = QPushButton("⎋  Open Ollama")
        btn_open.setCursor(Qt.PointingHandCursor)
        btn_open.setStyleSheet(
            "QPushButton{background-color: #FFFFFF; border: 1px solid #DCD5C5; border-radius: 10px;"
            "color: #1A1C1A; font-size: 12.5px; font-weight: 600; padding: 9px 18px;}"
            "QPushButton:hover{background-color: #F8F5EE;}"
        )
        btn_open.clicked.connect(self._on_open_ollama)

        btn_retry = QPushButton("↺  Retry Connection")
        btn_retry.setCursor(Qt.PointingHandCursor)
        btn_retry.setStyleSheet(
            "QPushButton{background-color: #FFD04D; border-radius: 10px;"
            "color: #1A1C1A; font-size: 12.5px; font-weight: 700; padding: 9px 20px; border: none;}"
            "QPushButton:hover{background-color: #E8B93A;}"
        )
        btn_retry.clicked.connect(self._on_retry)

        actions.addWidget(btn_cancel)
        actions.addWidget(btn_open)
        actions.addStretch(1)
        actions.addWidget(btn_retry)
        card_lay.addLayout(actions)

        outer.addWidget(card)

    def _on_retry(self):
        self.retryRequested.emit()
        self.accept()

    def _on_open_ollama(self):
        self.openOllamaRequested.emit()
        import webbrowser
        webbrowser.open("http://localhost:11434")


class UnsupportedFileDialog(QDialog):
    """
    Unsupported file type modal matching 'Unsupported File Type Dialog in GemmaNotepad1-2.png'.
    """

    chooseAnotherRequested = Signal()

    def __init__(self, filename: str = "document.xyz", file_size: str = "1.2 MB", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.resize(560, 490)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)

        card = QWidget()
        card.setObjectName("unsupportedCard")
        card.setAttribute(Qt.WA_StyledBackground, True)
        card.setStyleSheet(
            "#unsupportedCard{"
            "background-color: #FFFDF8; border: 1px solid #EDD89A; border-radius: 20px;"
            "}"
        )
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(28, 22, 28, 22)
        card_lay.setSpacing(14)

        # Header
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        icon_box = QFrame()
        icon_box.setFixedSize(40, 40)
        icon_box.setStyleSheet("background-color: #E53935; border-radius: 10px;")
        ib_lay = QVBoxLayout(icon_box)
        ib_lay.setContentsMargins(0, 0, 0, 0)
        ib_lbl = QLabel("✕")
        ib_lbl.setAlignment(Qt.AlignCenter)
        ib_lbl.setStyleSheet("color: #FFFFFF; font-size: 18px; font-weight: bold; background: transparent;")
        ib_lay.addWidget(ib_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        lbl_title = QLabel("Unsupported File Type")
        lbl_title.setStyleSheet("color: #1A1C1A; font-size: 18px; font-weight: 800; font-family: 'Segoe UI', sans-serif; background: transparent;")
        lbl_sub = QLabel("The file you selected cannot be opened in GemmaNotepad1.")
        lbl_sub.setStyleSheet("color: #7A7465; font-size: 12px; background: transparent;")
        title_col.addWidget(lbl_title)
        title_col.addWidget(lbl_sub)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(28, 28)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet(
            "QPushButton{background-color: #F6ECCF; border-radius: 14px; color: #5A5445;"
            "font-size: 13px; font-weight: 700; border: none;}"
            "QPushButton:hover{background-color: #EEDBBA; color: #1A1C1A;}"
        )
        btn_close.clicked.connect(self.reject)

        top_row.addWidget(icon_box)
        top_row.addLayout(title_col, 1)
        top_row.addWidget(btn_close)
        card_lay.addLayout(top_row)

        # File preview card (soft red tint)
        file_card = QFrame()
        file_card.setStyleSheet("background-color: #FDECEC; border: 1px solid #F5C6CB; border-radius: 12px;")
        fc_lay = QHBoxLayout(file_card)
        fc_lay.setContentsMargins(14, 10, 14, 10)
        fc_lay.setSpacing(12)

        doc_ico = QLabel("📄")
        doc_ico.setStyleSheet("font-size: 26px; background: transparent;")

        fc_info = QVBoxLayout()
        fc_info.setSpacing(2)
        lbl_fname = QLabel(filename)
        lbl_fname.setStyleSheet("color: #1A1C1A; font-size: 13px; font-weight: 700; background: transparent;")
        ext = os.path.splitext(filename)[1].upper()
        lbl_desc = QLabel(f"{ext or 'Unsupported'} File  •  {file_size}")
        lbl_desc.setStyleSheet("color: #7A7465; font-size: 11.5px; background: transparent;")
        fc_info.addWidget(lbl_fname)
        fc_info.addWidget(lbl_desc)

        fc_lay.addWidget(doc_ico)
        fc_lay.addLayout(fc_info, 1)
        card_lay.addWidget(file_card)

        # Supported formats list
        lbl_supp = QLabel("ℹ  GemmaNotepad1 currently supports the following file formats:")
        lbl_supp.setStyleSheet("color: #1A1C1A; font-size: 12px; font-weight: 600; background: transparent;")
        card_lay.addWidget(lbl_supp)

        fmt_row = QHBoxLayout()
        fmt_row.setSpacing(8)

        fmts = [
            ("PDF", "#E53935", ".pdf", "Recommended\n(read, summarize, quiz)"),
            ("TXT", "#455A64", ".txt", "Plain text files\n(read, summarize)"),
            ("MD", "#1E88E5", ".md", "Markdown files\n(read, summarize)")
        ]
        for badge_t, color, name_t, desc_t in fmts:
            c = QFrame()
            c.setStyleSheet("background-color: #FFFDF8; border: 1px solid #EDD89A; border-radius: 10px;")
            cl = QHBoxLayout(c)
            cl.setContentsMargins(10, 8, 10, 8)
            cl.setSpacing(8)
            b = QLabel(badge_t)
            b.setFixedSize(28, 28)
            b.setAlignment(Qt.AlignCenter)
            b.setStyleSheet(f"background-color: {color}; color: #FFFFFF; font-size: 9px; font-weight: bold; border-radius: 5px;")
            ci = QVBoxLayout()
            ci.setSpacing(1)
            lt = QLabel(name_t)
            lt.setStyleSheet("color: #1A1C1A; font-size: 12px; font-weight: 700; background: transparent;")
            ld = QLabel(desc_t)
            ld.setStyleSheet("color: #7A7465; font-size: 10px; line-height: 1.2; background: transparent;")
            ci.addWidget(lt)
            ci.addWidget(ld)
            cl.addWidget(b)
            cl.addLayout(ci, 1)
            fmt_row.addWidget(c, 1)
        card_lay.addLayout(fmt_row)

        # Tip card
        tip_card = QFrame()
        tip_card.setStyleSheet("background-color: #FEF9E7; border: 1px solid #F5E5B8; border-radius: 12px;")
        tc_lay = QVBoxLayout(tip_card)
        tc_lay.setContentsMargins(14, 10, 14, 10)
        tc_lay.setSpacing(4)
        th = QHBoxLayout()
        th.addWidget(QLabel("💡"))
        lbl_th = QLabel("Need to use this file?")
        lbl_th.setStyleSheet("color: #1A1C1A; font-size: 12.5px; font-weight: 700; background: transparent;")
        th.addWidget(lbl_th)
        th.addStretch(1)
        tc_lay.addLayout(th)
        lbl_tt = QLabel("You can convert your file to PDF or TXT and try again.")
        lbl_tt.setStyleSheet("color: #5A5445; font-size: 11.5px; background: transparent;")
        tc_lay.addWidget(lbl_tt)
        card_lay.addWidget(tip_card)

        # Actions
        actions = QHBoxLayout()
        actions.setSpacing(10)

        btn_choose = QPushButton("📁  Choose Another File")
        btn_choose.setCursor(Qt.PointingHandCursor)
        btn_choose.setStyleSheet(
            "QPushButton{background-color: #FFFFFF; border: 1px solid #DCD5C5; border-radius: 10px;"
            "color: #1A1C1A; font-size: 12.5px; font-weight: 600; padding: 9px 18px;}"
            "QPushButton:hover{background-color: #F8F5EE;}"
        )
        btn_choose.clicked.connect(self._on_choose_another)

        btn_close_act = QPushButton("Close")
        btn_close_act.setCursor(Qt.PointingHandCursor)
        btn_close_act.setStyleSheet(
            "QPushButton{background-color: #FFD04D; border-radius: 10px;"
            "color: #1A1C1A; font-size: 12.5px; font-weight: 700; padding: 9px 22px; border: none;}"
            "QPushButton:hover{background-color: #E8B93A;}"
        )
        btn_close_act.clicked.connect(self.accept)

        actions.addWidget(btn_choose)
        actions.addStretch(1)
        actions.addWidget(btn_close_act)
        card_lay.addLayout(actions)

        outer.addWidget(card)

    def _on_choose_another(self):
        self.chooseAnotherRequested.emit()
        self.accept()
