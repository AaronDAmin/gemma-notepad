"""Quiz generation via Ollama — builds prompt, calls model, validates JSON."""
from __future__ import annotations
import json
import re
from app.services.ollama_service import ollama_service


class QuizService:

    def build_prompt(self, text: str, num_questions: int,
                     difficulty: str, focus: str) -> str:
        return f"""You are a quiz generator. Based on the following document text, generate exactly {num_questions} multiple-choice questions.

Difficulty: {difficulty}
Focus: {focus}

Document text:
---
{text[:6000]}
---

Return ONLY a valid JSON array, no explanation, no markdown, no code block. Format:
[
  {{
    "question": "Question text here?",
    "options": {{
      "A": "First option",
      "B": "Second option",
      "C": "Third option",
      "D": "Fourth option"
    }},
    "correct": "B",
    "explanation": "Brief explanation of the correct answer."
  }}
]"""

    def generate(self, model: str, text: str, num_questions: int,
                 difficulty: str, focus: str) -> list[dict]:
        """Generate quiz questions. Returns list of question dicts."""
        prompt = self.build_prompt(text, num_questions, difficulty, focus)
        raw = ollama_service.generate(model, prompt)
        return self._parse(raw, num_questions)

    def _parse(self, raw: str, expected: int) -> list[dict]:
        """Extract and validate JSON from model response."""
        # Strip markdown code blocks if present
        raw = re.sub(r"```(?:json)?", "", raw).strip()

        # Find the JSON array
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if not match:
            raise ValueError("Model did not return a JSON array.")

        data = json.loads(match.group())

        validated = []
        for i, q in enumerate(data):
            if not all(k in q for k in ("question", "options", "correct", "explanation")):
                continue
            if q["correct"] not in ("A", "B", "C", "D"):
                continue
            opts = q["options"]
            if not all(k in opts for k in ("A", "B", "C", "D")):
                continue
            validated.append(q)

        if not validated:
            raise ValueError("No valid questions found in model response.")

        return validated[:expected]


quiz_service = QuizService()
