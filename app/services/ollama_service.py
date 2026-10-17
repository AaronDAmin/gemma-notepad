"""Ollama local API client with automatic host discovery."""
from __future__ import annotations
import httpx
from app.core.config import OLLAMA_TIMEOUT

# Candidates tried in order — first one that responds wins
_CANDIDATE_HOSTS = [
    "http://127.0.0.1:11434",       # local (Linux running the app itself)
    "http://localhost:11434",        # local alias
    "http://10.10.248.23:11434",     # remote Linux on WiFi
]


def _discover_host() -> str | None:
    """Return the first reachable Ollama host, or None."""
    for host in _CANDIDATE_HOSTS:
        try:
            r = httpx.get(f"{host}/api/tags", timeout=2)
            if r.status_code == 200:
                return host
        except Exception:
            continue
    return None


class OllamaService:

    def __init__(self):
        self._active_host: str | None = None

    def _host(self) -> str | None:
        """Return cached host or rediscover."""
        if self._active_host:
            # Quick liveness check on cached host
            try:
                httpx.get(f"{self._active_host}/api/tags", timeout=2)
                return self._active_host
            except Exception:
                self._active_host = None   # cached host died, rediscover

        self._active_host = _discover_host()
        return self._active_host

    def is_running(self) -> bool:
        return self._host() is not None

    def active_host(self) -> str:
        return self._active_host or "Not connected"

    def list_models(self) -> list[str]:
        host = self._host()
        if not host:
            return []
        try:
            r = httpx.get(f"{host}/api/tags", timeout=5)
            r.raise_for_status()
            return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            return []

    def generate(self, model: str, prompt: str) -> str:
        host = self._host()
        if not host:
            raise RuntimeError(
                "Ollama is not reachable.\n"
                "Make sure Ollama is running on this machine or on the network."
            )
        try:
            r = httpx.post(
                f"{host}/api/generate",
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
