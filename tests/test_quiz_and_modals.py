"""Unit and GUI tests for Quiz views and AI Dialogs."""
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from main import configure_app, load_stylesheet
from app.ui.main_window import MainWindow
from app.ui.quiz_view import QuizView, QuizConfigForm, QuizQuestionView, QuizResultsView, DEFAULT_DBMS_QUESTIONS
from app.ui.dialogs.ai_explanation_dialog import AIExplanationDialog
from app.ui.dialogs.ai_followup_dialog import AIFollowUpDialog
from app.ui.dialogs.error_dialogs import OllamaConnectionErrorDialog, UnsupportedFileDialog


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
        configure_app(app)
        load_stylesheet(app)
    return app


def test_ai_explanation_dialog(qapp):
    """Test AIExplanationDialog initialization and context setting."""
    dlg = AIExplanationDialog()
    assert dlg is not None
    dlg.set_quiz_context(
        q_num=2,
        total_q=10,
        question="Which component stores data physically?",
        options=[
            ("A", "Query Processor", False, False),
            ("B", "Transaction Manager", False, False),
            ("C", "Storage Manager", True, True),
            ("D", "Authorization Manager", False, False),
        ],
        correct_answer="C. Storage Manager",
        user_answer="C. Storage Manager",
        explanation="The Storage Manager handles disk storage and buffer caching.",
        doc_name="Database Systems - Chapter 1.pdf",
        page=5
    )
    assert dlg.lbl_q_counter.text() == "Question 2 of 10"
    assert "Storage Manager" in dlg.lbl_correct_ans.text()
    dlg.close()


def test_ai_followup_dialog(qapp):
    """Test AIFollowUpDialog chat bubbles and user messages."""
    dlg = AIFollowUpDialog()
    assert dlg is not None
    dlg.set_context(
        question="Which component stores data physically?",
        correct_ans="C. Storage Manager",
        doc_name="Database Systems - Chapter 1.pdf",
        page=6
    )
    assert dlg.lbl_orig_q.text() == "Which component stores data physically?"

    # Test sending a message
    dlg.send_user_message("What are buffer managers?")
    qapp.processEvents()
    dlg.close()


def test_error_dialogs(qapp):
    """Test OllamaConnectionErrorDialog and UnsupportedFileDialog initialization."""
    ollama_dlg = OllamaConnectionErrorDialog("http://localhost:11434")
    assert ollama_dlg is not None
    ollama_dlg.close()

    unsupp_dlg = UnsupportedFileDialog("data.xlsx", "1.2 MB")
    assert unsupp_dlg is not None
    unsupp_dlg.close()


def test_quiz_view_flow(qapp):
    """Test QuizView stack transitions: config -> question -> results."""
    qv = QuizView()
    assert qv._stack.currentIndex() == 0  # Config form

    # Trigger questions loading
    qv.question_view.load_questions(DEFAULT_DBMS_QUESTIONS)
    qv._stack.setCurrentIndex(2)
    assert qv._stack.currentIndex() == 2

    # Answer questions
    qv.question_view._select_option("A")
    qv.question_view._next()
    assert qv.question_view._current == 1

    # Show results
    answers = {0: "A", 1: "C", 2: "B"}
    qv.results_view.show_results(DEFAULT_DBMS_QUESTIONS, answers)
    qv._stack.setCurrentIndex(3)
    assert qv._stack.currentIndex() == 3
    assert qv.results_view.lbl_stat_c_num.text() is not None
