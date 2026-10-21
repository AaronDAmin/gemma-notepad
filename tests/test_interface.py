"""Unit and GUI tests for the GemmaNotepad1 interface."""
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPoint

from main import configure_app, load_stylesheet
from app.ui.main_window import MainWindow
from app.ui.tab_bar import TabBar, DocumentTab
from app.ui.sidebar import Sidebar
from app.ui.upload_dialog import UploadPanel
from app.ui.pdf_viewer import PDFViewer
from app.ui.image_viewer import ImageViewer
from app.ui.text_editor import TextEditor
from app.ui.ai_popup import AIContextPopup


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
        configure_app(app)
        load_stylesheet(app)
    return app


def test_main_window_initialization(qapp):
    """Verify MainWindow initializes with exact initial state."""
    window = MainWindow()
    window.show()
    import time
    time.sleep(0.1)
    qapp.processEvents()


    assert window is not None
    assert window.windowFlags() & Qt.FramelessWindowHint

    # Verify tabs exist
    assert window.tab_bar.count() == 3
    assert window.tab_bar.active_tab_id() is not None

    # Verify Sidebar initial state
    assert window.sidebar._active_tool == "select"
    assert window.sidebar.btn_select._active is True
    assert window.sidebar.btn_upload._active is False
    assert window.sidebar.btn_quiz._active is False

    # Verify Upload panel is visible by default
    assert window.workspace.is_upload_visible() is True
    assert not window.workspace.upload_panel.isHidden()

    # Verify PDF is loaded in Tab 1
    assert window.workspace.current_mode() == 1  # MODE_PDF
    assert window.workspace.pdf_viewer._doc is not None
    assert window.workspace.pdf_viewer._total_pages == 20

    window.close()


def test_tab_bar_interactions(qapp):
    """Test adding, switching, and closing tabs."""
    tab_bar = TabBar()
    assert tab_bar.count() == 0

    tab_bar.add_tab(1, "Cours 01", activate=True)
    tab_bar.add_tab(2, "Cours 02", activate=False)
    tab_bar.add_tab(3, "Notes", activate=False)

    assert tab_bar.count() == 3
    assert tab_bar.active_tab_id() == 1
    assert tab_bar._tabs[1]._active is True
    assert tab_bar._tabs[2]._active is False

    # Switch to tab 2
    tab_bar.set_active_tab(2)
    assert tab_bar.active_tab_id() == 2
    assert tab_bar._tabs[1]._active is False
    assert tab_bar._tabs[2]._active is True

    # Close tab 2
    tab_bar.remove_tab(2)
    assert tab_bar.count() == 2
    assert tab_bar.active_tab_id() == 3


def test_sidebar_tool_switching(qapp):
    """Test sidebar tool button activations."""
    sidebar = Sidebar()
    assert sidebar._active_tool == "select"

    sidebar.btn_quiz.clicked.emit()
    assert sidebar._active_tool == "quiz"
    assert sidebar.btn_quiz._active is True
    assert sidebar.btn_select._active is False

    sidebar.btn_recent.clicked.emit()
    assert sidebar._active_tool == "recent"
    assert sidebar.btn_recent._active is True
    assert sidebar.btn_quiz._active is False

    sidebar.btn_library.clicked.emit()
    assert sidebar._active_tool == "library"
    assert sidebar.btn_library._active is True
    assert sidebar.btn_recent._active is False

    sidebar.btn_select.clicked.emit()
    assert sidebar._active_tool == "select"
    assert sidebar.btn_select._active is True


def test_workspace_navigation(qapp):
    """Test switching between views in the workspace stack."""
    window = MainWindow()
    window.show()
    qapp.processEvents()

    # Recent view
    window.sidebar.btn_recent.clicked.emit()
    assert window.workspace.current_mode() == 5
    assert window.sidebar._active_tool == "recent"

    # Library view
    window.sidebar.btn_library.clicked.emit()
    assert window.workspace.current_mode() == 6
    assert window.sidebar._active_tool == "library"

    # Select returns to document
    window.sidebar.btn_select.clicked.emit()
    assert window.workspace.current_mode() == 1  # PDF
    assert window.sidebar._active_tool == "select"

    window.close()


def test_upload_panel_toggle(qapp):
    """Test upload panel toggle and card options."""
    window = MainWindow()
    window.show()
    qapp.processEvents()

    assert window.workspace.is_upload_visible() is True

    # Toggle hide
    window.workspace.toggle_upload_panel()
    assert window.workspace.is_upload_visible() is False
    assert window.workspace.upload_panel.isHidden()

    # Toggle show
    window.workspace.toggle_upload_panel()
    assert window.workspace.is_upload_visible() is True
    assert not window.workspace.upload_panel.isHidden()

    window.close()


def test_ai_popup_anchor(qapp):
    """Test AI popup positioning and anchor."""
    window = MainWindow()
    window.show()
    qapp.processEvents()

    popup = window.ai_popup
    assert popup is not None

    # Test show_near
    target_pos = QPoint(400, 300)
    popup.show_near(target_pos, "database management system (DBMS)", "", "DBMS_Chapter1.pdf")
    qapp.processEvents()

    assert popup.isVisible() is True
    assert popup._selected_text == "database management system (DBMS)"

    popup.hide()
    assert popup.isVisible() is False
    window.close()


def test_image_viewer_functionality(qapp):
    """Test image loading, rotation, and zooming."""
    viewer = ImageViewer()
    import os
    from app.core.config import ASSETS_DIR
    er_path = str(ASSETS_DIR / "ER_Diagram.jpg")
    if os.path.exists(er_path):
        viewer.load_image(er_path)
        assert viewer._pixmap is not None
        assert viewer.filename_lbl.text() == "ER_Diagram.jpg"

        # Rotation
        viewer.rotate_right()
        assert viewer._rotation == 90
        viewer.rotate_left()
        assert viewer._rotation == 0

        # Zoom
        initial_zoom = viewer._zoom
        viewer._zoom_in()
        assert viewer._zoom > initial_zoom
        viewer._zoom_out()


def test_text_editor_functionality(qapp):
    """Test rich study note editor actions."""
    editor = TextEditor()
    editor.set_title("Test Note")
    assert editor.get_title() == "Test Note"

    editor.set_content("Database Normalization Concepts")
    assert "Normalization" in editor.get_content()

    editor._toggle_bold()
    editor._insert_bullet_list()
    editor._insert_code()
    assert editor.editor.toPlainText() is not None
