"""Ollama local API client."""
from __future__ import annotations
import httpx
from app.core.config import OLLAMA_BASE_URL, OLLAMA_TIMEOUT


class OllamaService:

    def is_running(self) -> bool:
        try:
            r = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    def list_models(self) -> list[str]:
        try:
            r = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
            r.raise_for_status()
            return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            return []

    def generate(self, model: str, prompt: str) -> str:
        """Send a prompt and return the complete response text."""
        try:
            r = httpx.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=OLLAMA_TIMEOUT,
            )
            r.raise_for_status()
            return r.json().get("response", "")
        except httpx.TimeoutException:
            raise TimeoutError("Ollama did not respond in time.")
        except Exception as e:
            raise RuntimeError(f"Ollama error: {e}")


# Module-level singleton
ollama_service = OllamaService()
