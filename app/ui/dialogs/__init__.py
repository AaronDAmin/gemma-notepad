"""UI Dialogs package."""
from app.ui.dialogs.ai_explanation_dialog import AIExplanationDialog
from app.ui.dialogs.ai_followup_dialog import AIFollowUpDialog
from app.ui.dialogs.error_dialogs import OllamaConnectionErrorDialog, UnsupportedFileDialog

__all__ = [
    "AIExplanationDialog",
    "AIFollowUpDialog",
    "OllamaConnectionErrorDialog",
    "UnsupportedFileDialog"
]
