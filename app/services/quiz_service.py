"""Quiz generation via Ollama — optimized prompt for slow local models."""
from __future__ import annotations
import json
import re
from app.services.ollama_service import ollama_service

# Max text characters sent to the model — keep it short for CPU models
_MAX_TEXT_CHARS = 2000


class QuizService:

    def build_prompt(self, text: str, num_questions: int,
                     difficulty: str, focus: str) -> str:
        # Trim text to avoid slow generation on CPU models
        trimmed = text.strip()[:_MAX_TEXT_CHARS]

        return (
            f"Generate {num_questions} multiple-choice quiz questions "
            f"({difficulty} difficulty, focus: {focus}) "
            f"based on this text:\n\n{trimmed}\n\n"
            f"Reply with ONLY a JSON array. Each item must have exactly these keys: "
            f"question, options (A/B/C/D), correct (one letter), explanation.\n"
            f"Example: "
            f'[{{"question":"...","options":{{"A":"...","B":"...","C":"...","D":"..."}},'
            f'"correct":"A","explanation":"..."}}]'
        )

    def generate(self, model: str, text: str, num_questions: int,
                 difficulty: str, focus: str) -> list[dict]:
        prompt = self.build_prompt(text, num_questions, difficulty, focus)
        raw    = ollama_service.generate(model, prompt)
        return self._parse(raw, num_questions)

    def _parse(self, raw: str, expected: int) -> list[dict]:
        # Strip markdown fences
        raw = re.sub(r"```(?:json)?", "", raw).strip()
        raw = raw.replace("```", "")

        # Find JSON array
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if not match:
            raise ValueError(
                "The model did not return valid JSON.\n"
                "Try reducing the number of questions or restarting Ollama."
            )

        try:
            data = json.loads(match.group())
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON parse error: {e}")

        validated = []
        for q in data:
            if not isinstance(q, dict):
                continue
            if not all(k in q for k in ("question", "options", "correct", "explanation")):
                continue
            if q["correct"] not in ("A", "B", "C", "D"):
                continue
            opts = q.get("options", {})
            if not all(k in opts for k in ("A", "B", "C", "D")):
                continue
            validated.append(q)

        if not validated:
            raise ValueError(
                "No valid questions found in the model response.\n"
                "Try again — the model sometimes produces inconsistent output."
            )

        return validated[:expected]


quiz_service = QuizService()
