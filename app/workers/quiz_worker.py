"""Background worker for quiz generation."""
from PySide6.QtCore import QThread, Signal
from app.services.quiz_service import quiz_service


class QuizWorker(QThread):
    resultReady   = Signal(list)   # list of question dicts
    errorOccurred = Signal(str)

    def __init__(self, model: str, text: str, num_questions: int,
                 difficulty: str, focus: str, parent=None):
        super().__init__(parent)
        self._model         = model
        self._text          = text
        self._num_questions = num_questions
        self._difficulty    = difficulty
        self._focus         = focus

    def run(self):
        try:
            questions = quiz_service.generate(
                self._model, self._text,
                self._num_questions, self._difficulty, self._focus
            )
            self.resultReady.emit(questions)
        except Exception as e:
            self.errorOccurred.emit(str(e))
