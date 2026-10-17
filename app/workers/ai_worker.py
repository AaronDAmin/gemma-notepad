"""Background QThread worker for Ollama inference."""
from PySide6.QtCore import QThread, Signal
from app.services.ollama_service import ollama_service


class AIWorker(QThread):
    resultReady   = Signal(str)
    errorOccurred = Signal(str)

    def __init__(self, model: str, prompt: str, parent=None):
        super().__init__(parent)
        self._model  = model
        self._prompt = prompt

    def run(self):
        try:
            result = ollama_service.generate(self._model, self._prompt)
            self.resultReady.emit(result)
        except Exception as e:
            self.errorOccurred.emit(str(e))
