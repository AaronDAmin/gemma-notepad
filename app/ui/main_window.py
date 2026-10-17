"""Main application window."""
from __future__ import annotations
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QMessageBox, QFileDialog, QDialog, QComboBox,
    QLabel, QPushButton, QFormLayout, QDialogButtonBox
)
from PySide6.QtCore import Qt

from app.core.config import (
    APP_NAME, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    WINDOW_DEFAULT_W, WINDOW_DEFAULT_H
)
from app.core.database      import db
from app.core.models        import Document, DocumentType
from app.storage.repositories import doc_repo, settings_repo
from app.services.ollama_service import ollama_service
from app.ui.sidebar   import Sidebar
from app.ui.tab_bar   import TabBar
from app.ui.workspace import Workspace


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.resize(WINDOW_DEFAULT_W, WINDOW_DEFAULT_H)

        # Init DB
        db.initialize()

        self._active_model: str = ""

        self._setup_ui()
        self._wire_signals()
        self._init_tabs()
        self._load_settings()
        self._refresh_recent()

    # ── UI construction ────────────────────────────────────────────────────────

    def _setup_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.tab_bar = TabBar()
        root.addWidget(self.tab_bar)

        body = QWidget()
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(0)

        self.sidebar   = Sidebar()
        self.workspace = Workspace()

        body_lay.addWidget(self.sidebar)
        body_lay.addWidget(self.workspace, 1)
        root.addWidget(body, 1)

        # AI popup lives on MainWindow so it floats over everything
        from app.ui.ai_popup import AIContextPopup
        self.ai_popup = AIContextPopup(self)
        self.ai_popup.hide()

    def _wire_signals(self):
        self.tab_bar.tabSelected.connect(self._on_tab_selected)
        self.tab_bar.tabClosed.connect(self._on_tab_closed)
        self.tab_bar.newTabRequested.connect(self._on_new_tab)

        self.sidebar.selectClicked.connect(self._on_select_tool)
        self.sidebar.uploadClicked.connect(self._on_upload_tool)
        self.sidebar.quizClicked.connect(self._on_quiz_tool)
        self.sidebar.settingsClicked.connect(self._on_settings)

        self.workspace.pdfUploadRequested.connect(self._import_pdf)
        self.workspace.imageUploadRequested.connect(self._import_image)
        self.workspace.textUploadRequested.connect(self._new_text_note)

        # Text selection → AI popup
        self.workspace.pdf_viewer.textSelected.connect(self._on_text_selected)
        self.workspace.text_editor.textSelected.connect(
            lambda text: self._on_text_selected(text, -1)
        )

    def _init_tabs(self):
        self._workspaces: dict[int, dict] = {}
        self._next_tab_id = 1
        for name in ("Cours 01", "Cours 02", "Notes"):
            self._create_tab(name, activate=(name == "Cours 01"))
        self.workspace.show_pdf()
        self._workspaces[1]["mode"] = "pdf"

    def _load_settings(self):
        self._active_model = settings_repo.get("active_model", "")
        self.ai_popup.set_model(self._active_model)

    def _refresh_recent(self):
        recent = doc_repo.get_recent(limit=8)
        items = []
        for d in recent:
            if d.doc_type == DocumentType.PDF:
                icon, meta = "📄", f"PDF  •  {d.name}"
            elif d.doc_type == DocumentType.IMAGE:
                icon, meta = "🖼", f"Image  •  {d.name}"
            else:
                icon, meta = "📝", f"Text  •  {d.name}"
            items.append((icon, d.name, meta))
        self.workspace.upload_panel.refresh_recent(items)

    # ── Tab management ─────────────────────────────────────────────────────────

    def _create_tab(self, name: str, activate: bool = True) -> int:
        tab_id = self._next_tab_id
        self._next_tab_id += 1
        self._workspaces[tab_id] = {"name": name, "mode": "empty"}
        self.tab_bar.add_tab(tab_id, name, activate=activate)
        return tab_id

    def _on_new_tab(self):
        count = self.tab_bar.count() + 1
        self._create_tab(f"Cours {count:02d}")

    def _on_tab_selected(self, tab_id: int):
        ws   = self._workspaces.get(tab_id, {})
        mode = ws.get("mode", "empty")
        if mode == "pdf":
            self.workspace.show_pdf()
        elif mode == "image":
            self.workspace.show_image()
        elif mode == "text":
            self.workspace.show_text()
        else:
            self.workspace.show_empty()
        self.workspace.hide_upload_panel()

    def _on_tab_closed(self, tab_id: int):
        if self.tab_bar.count() <= 1:
            self.workspace.show_empty()
            return
        self._workspaces.pop(tab_id, None)
        self.tab_bar.remove_tab(tab_id)

    # ── Sidebar handlers ───────────────────────────────────────────────────────

    def _on_select_tool(self):
        if self.workspace.current_mode() == 4:
            self.workspace.return_from_quiz()
            self.sidebar.set_active_tool("select")

    def _on_upload_tool(self):
        self.workspace.toggle_upload_panel()
        if not self.workspace.is_upload_visible():
            self.sidebar.set_active_tool("select")

    def _on_quiz_tool(self):
        # Pass current model and PDF text to the quiz view
        pdf_text = ""
        doc_name = ""
        if self.workspace.pdf_viewer._doc is not None:
            from app.services.pdf_service import pdf_service
            doc  = self.workspace.pdf_viewer._doc
            pages = range(doc.page_count)
            pdf_text = "\n\n".join(
                "\n".join(b["text"] for b in pdf_service.get_text_blocks(doc, p))
                for p in pages
            )
            doc_name = self.workspace.pdf_viewer._doc_name

        self.workspace.quiz_view.set_context(
            self._active_model, pdf_text, doc_name
        )
        self.workspace.show_quiz()

    def _on_settings(self):
        self._open_settings_dialog()

    # ── Document import ────────────────────────────────────────────────────────

    def _import_pdf(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open PDF", "", "PDF Files (*.pdf)"
        )
        if not path:
            return
        self.workspace.hide_upload_panel()
        self.workspace.show_pdf()

        name = os.path.splitext(os.path.basename(path))[0]
        self.workspace.pdf_viewer.load_pdf(path, doc_name=name)

        active_id = self.tab_bar.active_tab_id()
        if active_id and active_id in self._workspaces:
            self._workspaces[active_id]["mode"] = "pdf"
            self._workspaces[active_id]["path"] = path
            self.tab_bar.rename_tab(active_id, name[:20])

        # Persist
        doc = Document(
            id=None, workspace_id=active_id or 1,
            name=name, doc_type=DocumentType.PDF,
            file_path=path,
            content=None,
            page_count=self.workspace.pdf_viewer._total_pages,
        )
        doc_repo.save(doc)
        self._refresh_recent()

    def _import_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if not path:
            return
        self.workspace.hide_upload_panel()
        self.workspace.show_image()
        self.workspace.image_viewer.load_image(path)

        name = os.path.splitext(os.path.basename(path))[0]
        active_id = self.tab_bar.active_tab_id()
        if active_id and active_id in self._workspaces:
            self._workspaces[active_id]["mode"] = "image"
            self._workspaces[active_id]["path"] = path
            self.tab_bar.rename_tab(active_id, name[:20])

        doc = Document(
            id=None, workspace_id=active_id or 1,
            name=name, doc_type=DocumentType.IMAGE,
            file_path=path, content=None,
        )
        doc_repo.save(doc)
        self._refresh_recent()

    def _new_text_note(self):
        self.workspace.hide_upload_panel()
        self.workspace.show_text()
        active_id = self.tab_bar.active_tab_id()
        if active_id and active_id in self._workspaces:
            self._workspaces[active_id]["mode"] = "text"
            self.tab_bar.rename_tab(active_id, "New Note")

        doc = Document(
            id=None, workspace_id=active_id or 1,
            name="New Note", doc_type=DocumentType.TEXT,
            file_path=None, content="",
        )
        doc_repo.save(doc)
        self._refresh_recent()

    # ── AI popup ───────────────────────────────────────────────────────────────

    def _on_text_selected(self, text: str, page_num: int):
        """Show the AI popup near the cursor when text is selected."""
        if not text.strip():
            return

        # Get context from the PDF viewer if applicable
        context = ""
        doc_name = ""
        if page_num >= 0:
            context  = self.workspace.pdf_viewer.get_context_for_selection(text)
            doc_name = self.workspace.pdf_viewer._doc_name

        # Position the popup at the current cursor position
        from PySide6.QtGui import QCursor
        cursor_pos = QCursor.pos()

        popup = self.ai_popup
        popup.set_model(self._active_model)
        popup.show_near(cursor_pos, text, context, doc_name)

    # ── Settings dialog ────────────────────────────────────────────────────────

    def _open_settings_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Settings")
        dlg.setMinimumWidth(360)
        dlg.setStyleSheet(
            "QDialog{background:#2E312E;}"
            "QLabel{color:#F0EDE8;font-size:13px;background:transparent;}"
            "QComboBox{background:#343834;border:1px solid #3D413D;"
            "border-radius:8px;color:#F0EDE8;padding:6px 10px;font-size:13px;}"
            "QComboBox::drop-down{border:none;width:20px;}"
            "QComboBox QAbstractItemView{background:#343834;color:#F0EDE8;"
            "selection-background-color:#D4A017;}"
            "QPushButton{background:#F0C94C;border-radius:8px;color:#1A1C1A;"
            "font-size:13px;font-weight:600;padding:7px 20px;border:none;}"
            "QPushButton:hover{background:#E8B93A;}"
        )

        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(20, 20, 20, 16)
        lay.setSpacing(14)

        # Ollama status
        running = ollama_service.is_running()
        host_str = ollama_service.active_host() if running else "Not connected"
        status_lbl = QLabel(
            f"Ollama:  {'✓ Running' if running else '✗ Not running'}  "
            f"{'(' + host_str + ')' if running else ''}"
        )
        status_lbl.setStyleSheet(
            f"color:{'#4CAF82' if running else '#E05555'};"
            "font-size:13px;font-weight:600;background:transparent;"
        )
        lay.addWidget(status_lbl)

        # Model selector
        model_lbl = QLabel("AI Model:")
        combo = QComboBox()
        if running:
            models = ollama_service.list_models()
            combo.addItems(models)
            if self._active_model in models:
                combo.setCurrentText(self._active_model)
        else:
            combo.addItem("No models available")
            combo.setEnabled(False)

        form = QFormLayout()
        form.setSpacing(8)
        form.addRow(model_lbl, combo)
        lay.addLayout(form)

        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.setStyleSheet(
            "QPushButton{background:#F0C94C;border-radius:8px;color:#1A1C1A;"
            "font-size:13px;font-weight:600;padding:7px 20px;border:none;}"
            "QPushButton:hover{background:#E8B93A;}"
        )
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        lay.addWidget(btns)

        if dlg.exec() == QDialog.Accepted and running:
            model = combo.currentText()
            self._active_model = model
            settings_repo.set("active_model", model)
            self.ai_popup.set_model(model)
            self.workspace.quiz_view.set_context(
                model,
                self.workspace.quiz_view._doc_text,
                self.workspace.quiz_view._doc_name
            )
