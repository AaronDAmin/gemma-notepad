"""Main application window."""
from __future__ import annotations
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QMessageBox, QFileDialog, QDialog, QComboBox,
    QLabel, QPushButton, QFormLayout, QDialogButtonBox, QSizeGrip
)
from PySide6.QtCore import Qt, QPoint, QRect, QTimer
from PySide6.QtGui import QCursor

from app.core.config import (
    APP_NAME, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    WINDOW_DEFAULT_W, WINDOW_DEFAULT_H, ROOT_DIR, ASSETS_DIR
)
from app.core.database      import db
from app.core.models        import Document, DocumentType
from app.storage.repositories import doc_repo, settings_repo
from app.services.ollama_service import ollama_service
from app.ui.sidebar   import Sidebar
from app.ui.tab_bar   import TabBar
from app.ui.workspace import Workspace
from app.ui.ai_popup  import AIContextPopup


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.resize(WINDOW_DEFAULT_W, 780)

        # Frameless window with custom title bar & rounded frame
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # Resize margin for frameless window
        self._resize_margin = 6
        self._resizing = False
        self._resize_direction = None

        # Init DB
        db.initialize()
        self._active_model: str = ""

        self._setup_ui()
        self._seed_default_data()
        self._wire_signals()
        self._init_tabs()
        self._load_settings()
        self._refresh_recent()

    def showEvent(self, event):
        super().showEvent(event)
        # Ensure layout is ready, then show initial state
        QTimer.singleShot(50, self._show_initial_state)


    def _setup_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        central.setStyleSheet(
            "#centralWidget{"
            "background-color: #202A27;"
            "border-radius: 16px;"
            "}"
        )
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.tab_bar = TabBar(self)
        root.addWidget(self.tab_bar)

        body = QWidget()
        body.setStyleSheet("background: transparent;")
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(0)

        self.sidebar   = Sidebar(self)
        self.workspace = Workspace(self)

        body_lay.addWidget(self.sidebar)
        body_lay.addWidget(self.workspace, 1)
        root.addWidget(body, 1)

        # AI popup floats over MainWindow
        self.ai_popup = AIContextPopup(self)
        self.ai_popup.hide()

    def _seed_default_data(self):
        """Ensure sample documents shown in reference image exist."""
        dbms_path = str(ASSETS_DIR / "DBMS_Chapter1.pdf")
        er_path   = str(ASSETS_DIR / "ER_Diagram.jpg")

        recent = doc_repo.get_recent(limit=10)
        existing_names = {d.name for d in recent}

        if "Notes - Normalization" not in existing_names:
            doc_repo.save(Document(
                id=None, workspace_id=1, name="Notes - Normalization",
                doc_type=DocumentType.TEXT, file_path=None,
                content="# Database Normalization\n\n1NF: Atomic values\n2NF: No partial dependency\n3NF: No transitive dependency\nBCNF: Boyce-Codd Normal Form",
                page_count=0, current_page=1, zoom_level=125
            ))

        if "ER_Diagram.jpg" not in existing_names and os.path.exists(er_path):
            doc_repo.save(Document(
                id=None, workspace_id=1, name="ER_Diagram.jpg",
                doc_type=DocumentType.IMAGE, file_path=er_path,
                content=None, page_count=0, current_page=1, zoom_level=125
            ))

        if "DBMS_Chapter1.pdf" not in existing_names and os.path.exists(dbms_path):
            doc_repo.save(Document(
                id=None, workspace_id=1, name="DBMS_Chapter1.pdf",
                doc_type=DocumentType.PDF, file_path=dbms_path,
                content=None, page_count=20, current_page=1, zoom_level=125
            ))

    def _wire_signals(self):
        # Window controls
        self.tab_bar.minimizeRequested.connect(self.showMinimized)
        self.tab_bar.maximizeRequested.connect(self._toggle_maximize)
        self.tab_bar.closeRequested.connect(self.close)

        # Tabs
        self.tab_bar.tabSelected.connect(self._on_tab_selected)
        self.tab_bar.tabClosed.connect(self._on_tab_closed)
        self.tab_bar.newTabRequested.connect(self._on_new_tab)

        # Sidebar
        self.sidebar.selectClicked.connect(self._on_select_tool)
        self.sidebar.uploadClicked.connect(self._on_upload_tool)
        self.sidebar.quizClicked.connect(self._on_quiz_tool)
        self.sidebar.recentClicked.connect(self._on_recent_tool)
        self.sidebar.libraryClicked.connect(self._on_library_tool)
        self.sidebar.settingsClicked.connect(self._on_settings_tool)
        self.sidebar.themeClicked.connect(self._on_theme_toggle)

        # Workspace & Upload
        self.workspace.pdfUploadRequested.connect(self._import_pdf)
        self.workspace.imageUploadRequested.connect(self._import_image)
        self.workspace.textUploadRequested.connect(self._new_text_note)
        self.workspace.upload_panel.documentRequested.connect(self._open_recent)
        self.workspace.text_editor.btn_save.clicked.connect(self._save_note)
        self.workspace.text_editor.editor.textChanged.connect(self._remember_note)

        # Central Views
        self.workspace.home_view.openPdfRequested.connect(self._import_pdf)
        self.workspace.home_view.importImageRequested.connect(self._import_image)
        self.workspace.home_view.newNoteRequested.connect(self._new_text_note)
        self.workspace.home_view.generateQuizRequested.connect(self._on_quiz_tool)
        self.workspace.home_view.documentOpened.connect(self._open_document)
        self.workspace.home_view.viewAllRecentRequested.connect(self._on_recent_tool)

        self.workspace.recent_view.documentOpened.connect(self._open_document)
        self.workspace.library_view.documentOpened.connect(self._open_document)
        self.workspace.library_view.uploadRequested.connect(self._on_upload_tool)
        self.workspace.search_view.openDocumentAtPage.connect(self._open_document_at_page)
        self.workspace.pdf_viewer.toolbar.searchClicked.connect(self._on_search_tool)
        self.workspace.settings_view.modelChanged.connect(self._on_model_changed)

        # Text selection → AI popup
        self.workspace.pdf_viewer.textSelected.connect(self._on_text_selected)
        self.workspace.text_editor.textSelected.connect(
            lambda text: self._on_text_selected(text, -1)
        )

    def _init_tabs(self):
        self._workspaces: dict[int, dict] = {}
        self._next_tab_id = 1

        dbms_path = str(ASSETS_DIR / "DBMS_Chapter1.pdf")

        # Tab 1: Cours 01 (active, DBMS Chapter 1)
        t1 = self._create_tab("Cours 01", activate=True)
        self._workspaces[t1].update(
            mode="pdf",
            path=dbms_path if os.path.exists(dbms_path) else None,
            name="DBMS_Chapter1"
        )

        # Tab 2: Cours 02 (inactive)
        t2 = self._create_tab("Cours 02", activate=False)
        self._workspaces[t2].update(mode="empty", name="Cours 02")

        # Tab 3: Notes (inactive)
        t3 = self._create_tab("Notes", activate=False)
        self._workspaces[t3].update(mode="text", name="Notes", content="")

        # Ensure Tab 1 is active
        self.tab_bar.set_active_tab(t1)

    def _show_initial_state(self):
        """Initial display matching the reference mockup."""
        dbms_path = str(ASSETS_DIR / "DBMS_Chapter1.pdf")
        if os.path.exists(dbms_path):
            self.workspace.show_pdf()
            self.workspace.pdf_viewer.load_pdf(dbms_path, "DBMS_Chapter1.pdf")

            # Highlight phrase
            phrase = "database management system (DBMS)"
            hr = self.workspace.pdf_viewer.highlight_phrase(phrase)
            if hr:
                # Position AI popup centered right above the highlight
                page_w = self.workspace.pdf_viewer.page_widget
                g_pos = page_w.mapToGlobal(QPoint(hr.center().x(), hr.top()))
                self.ai_popup.show_near(g_pos, phrase, "", "DBMS_Chapter1.pdf")

    def _load_settings(self):
        self._active_model = settings_repo.get("active_model", "")
        self.ai_popup.set_model(self._active_model)

    def _refresh_recent(self):
        recent = doc_repo.get_recent(limit=8)
        self._recent_documents = {d.id: d for d in recent}
        items = []
        for d in recent:
            if d.doc_type == DocumentType.PDF:
                meta = "12 pages  •  2 hours ago" if "DBMS" in d.name else f"{d.page_count} pages  •  Recent"
                items.append(("PDF", d.name, meta, d.id))
            elif d.doc_type == DocumentType.IMAGE:
                items.append(("IMAGE", d.name, "Image  •  1 day ago", d.id))
            else:
                items.append(("TEXT", d.name, "Text  •  2 days ago", d.id))
        self.workspace.upload_panel.refresh_recent(items)
        self.workspace.home_view.refresh_recent()
        self.workspace.recent_view.refresh()
        self.workspace.library_view.refresh()

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    # ── Tab management ─────────────────────────────────────────────────────────

    def _create_tab(self, name: str, activate: bool = True) -> int:
        tab_id = self._next_tab_id
        self._next_tab_id += 1
        self._workspaces[tab_id] = {"name": name, "mode": "empty"}
        self.tab_bar.add_tab(tab_id, name, activate=activate)
        return tab_id

    def _on_new_tab(self):
        count = self.tab_bar.count() + 1
        self._create_tab(f"Cours {count:02d}", activate=True)

    def _on_tab_selected(self, tab_id: int):
        self.sidebar.set_active_tool("select")
        ws   = self._workspaces.get(tab_id, {})
        mode = ws.get("mode", "empty")
        if mode == "pdf":
            if ws.get("path"):
                self.workspace.pdf_viewer.load_pdf(ws["path"], doc_name=ws["name"])
            self.workspace.show_pdf()
        elif mode == "image":
            self.ai_popup.hide()
            if ws.get("path"):
                self.workspace.image_viewer.load_image(ws["path"])
            self.workspace.show_image()
        elif mode == "text":
            self.ai_popup.hide()
            self.workspace.text_editor.set_content(ws.get("content", ""))
            self.workspace.show_text()
        else:
            self.ai_popup.hide()
            self.workspace.show_home()

    def _on_tab_closed(self, tab_id: int):
        self._workspaces.pop(tab_id, None)
        self.tab_bar.remove_tab(tab_id)
        if not self.tab_bar.count():
            self.workspace.show_empty()

    def _ensure_tab(self):
        if self.tab_bar.active_tab_id() is None:
            self._on_new_tab()

    def _open_recent(self, document_id: int):
        doc = self._recent_documents.get(document_id)
        if doc is None:
            return
        if doc.doc_type != DocumentType.TEXT and not os.path.isfile(doc.file_path or ""):
            QMessageBox.warning(self, "Document unavailable", "This file has been moved or deleted.")
            return
        for tab_id, state in self._workspaces.items():
            if state.get("document_id") == document_id:
                self.tab_bar.set_active_tab(tab_id)
                return
        tab_id = self._create_tab(doc.name, activate=False)
        self._workspaces[tab_id].update(
            mode=doc.doc_type.value, path=doc.file_path,
            content=doc.content or "", document_id=doc.id, document=doc,
        )
        self.tab_bar.set_active_tab(tab_id)

    def _remember_note(self):
        state = self._workspaces.get(self.tab_bar.active_tab_id(), {})
        if state.get("mode") == "text":
            state["content"] = self.workspace.text_editor.get_content()

    def _save_note(self):
        state = self._workspaces.get(self.tab_bar.active_tab_id(), {})
        if state.get("mode") != "text":
            return
        doc = state.get("document")
        if doc is not None:
            doc.content = self.workspace.text_editor.get_content()
            doc_repo.save(doc)
            self._refresh_recent()

    def _on_select_tool(self):
        active_id = self.tab_bar.active_tab_id()
        if active_id and active_id in self._workspaces:
            self._on_tab_selected(active_id)
        else:
            self.workspace.show_home()
        self.sidebar.set_active_tool("select")

    def _on_upload_tool(self):
        self.workspace.toggle_upload_panel()
        if not self.workspace.is_upload_visible():
            self.sidebar.set_active_tool("select")

    def _on_quiz_tool(self):
        self.ai_popup.hide()
        pdf_viewer = self.workspace.pdf_viewer
        doc_name   = ""
        total_pages = 0
        current_page = 1

        if pdf_viewer._doc is not None:
            doc_name     = pdf_viewer._doc_name
            total_pages  = pdf_viewer._total_pages
            current_page = pdf_viewer._current_page + 1

        self.workspace.quiz_view.set_context(
            model        = self._active_model,
            doc          = pdf_viewer._doc,
            doc_name     = doc_name,
            total_pages  = total_pages,
            current_page = current_page,
        )
        self.workspace.show_quiz()
        self.sidebar.set_active_tool("quiz")

    def _on_recent_tool(self):
        self.ai_popup.hide()
        self.workspace.show_recent()
        self.sidebar.set_active_tool("recent")

    def _on_library_tool(self):
        self.ai_popup.hide()
        self.workspace.show_library()
        self.sidebar.set_active_tool("library")

    def _on_search_tool(self):
        self.ai_popup.hide()
        self.workspace.show_search()
        self.sidebar.set_active_tool("")

    def _on_settings_tool(self):
        self.ai_popup.hide()
        self.workspace.show_settings()
        self.sidebar.set_active_tool("")

    def _on_settings(self):
        self.ai_popup.hide()
        self.workspace.show_settings()
        self.sidebar.set_active_tool("")

    def _on_model_changed(self, model: str):
        self._active_model = model
        self.ai_popup.set_model(model)
        qv = self.workspace.quiz_view
        qv.set_context(
            model        = model,
            doc          = qv._doc,
            doc_name     = qv._doc_name,
            total_pages  = qv._total_pages,
            current_page = qv._current_page,
        )

    def _open_document(self, doc: Document):
        if doc is None:
            return
        if doc.doc_type != DocumentType.TEXT and not (doc.file_path and os.path.isfile(doc.file_path)):
            QMessageBox.warning(self, "Document unavailable", "This file has been moved or deleted.")
            return

        for tab_id, state in self._workspaces.items():
            if state.get("document_id") == doc.id or (doc.file_path and state.get("path") == doc.file_path):
                self.tab_bar.set_active_tab(tab_id)
                self.sidebar.set_active_tool("select")
                return

        tab_id = self._create_tab(doc.name, activate=False)
        self._workspaces[tab_id].update(
            mode=doc.doc_type.value, path=doc.file_path,
            content=doc.content or "", document_id=doc.id, document=doc,
        )
        self.tab_bar.set_active_tab(tab_id)
        self.sidebar.set_active_tool("select")

    def _open_document_at_page(self, doc: Document, page: int):
        self._open_document(doc)
        if doc.doc_type == DocumentType.PDF:
            self.workspace.pdf_viewer.go_to_page(page - 1)

    def _on_theme_toggle(self):
        pass

    # ── Document import ────────────────────────────────────────────────────────

    def _import_pdf(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open PDF", "", "PDF Files (*.pdf)"
        )
        if not path:
            return
        self._ensure_tab()
        self.workspace.show_pdf()

        name = os.path.splitext(os.path.basename(path))[0]
        self.workspace.pdf_viewer.load_pdf(path, doc_name=name)

        active_id = self.tab_bar.active_tab_id()
        if active_id and active_id in self._workspaces:
            self._workspaces[active_id]["mode"] = "pdf"
            self._workspaces[active_id]["path"] = path
            self.tab_bar.rename_tab(active_id, name[:20])

        doc = Document(
            id=None, workspace_id=active_id or 1,
            name=name, doc_type=DocumentType.PDF,
            file_path=path,
            content=None,
            page_count=self.workspace.pdf_viewer._total_pages,
        )
        doc.id = doc_repo.save(doc)
        if active_id in self._workspaces:
            self._workspaces[active_id].update(document_id=doc.id, document=doc, name=doc.name)
        self._refresh_recent()

    def _import_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if not path:
            return
        self._ensure_tab()
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
        doc.id = doc_repo.save(doc)
        if active_id in self._workspaces:
            self._workspaces[active_id].update(document_id=doc.id, document=doc, name=doc.name)
        self._refresh_recent()

    def _new_text_note(self):
        self._ensure_tab()
        self.workspace.text_editor.set_content("")
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
        doc.id = doc_repo.save(doc)
        if active_id in self._workspaces:
            self._workspaces[active_id].update(document_id=doc.id, document=doc, name=doc.name)
        self._refresh_recent()

    # ── AI popup ───────────────────────────────────────────────────────────────

    def _on_text_selected(self, text: str, page_num: int):
        if not text.strip():
            return

        context = ""
        doc_name = ""
        if page_num >= 0:
            context  = self.workspace.pdf_viewer.get_context_for_selection(text)
            doc_name = self.workspace.pdf_viewer._doc_name

        cursor_pos = QCursor.pos()
        self.ai_popup.set_model(self._active_model)
        self.ai_popup.show_near(cursor_pos, text, context, doc_name)

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
            "QPushButton{background:#FFD04D;border-radius:8px;color:#1A1C1A;"
            "font-size:13px;font-weight:600;padding:7px 20px;border:none;}"
            "QPushButton:hover{background:#E8B93A;}"
        )

        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(20, 20, 20, 16)
        lay.setSpacing(14)

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

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.setStyleSheet(
            "QPushButton{background:#FFD04D;border-radius:8px;color:#1A1C1A;"
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
            qv = self.workspace.quiz_view
            qv.set_context(
                model=model,
                doc=qv._doc,
                doc_name=qv._doc_name,
                total_pages=qv._total_pages,
                current_page=qv._current_page,
            )
