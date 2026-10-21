"""Application-wide configuration constants."""
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT_DIR    = Path(__file__).resolve().parents[2]
ASSETS_DIR  = ROOT_DIR / "assets"
STYLES_DIR  = ASSETS_DIR / "styles"
ICONS_DIR   = ASSETS_DIR / "icons"
DATA_DIR    = ROOT_DIR / "data"
DB_PATH     = DATA_DIR / "study_notepad.db"

DATA_DIR.mkdir(exist_ok=True)

# ── Application meta ───────────────────────────────────────────────────────────
APP_NAME    = "GemmaNotepad1"
APP_VERSION = "0.1.0"

# ── Window defaults ────────────────────────────────────────────────────────────
WINDOW_MIN_WIDTH  = 960
WINDOW_MIN_HEIGHT = 620
WINDOW_DEFAULT_W  = 1200
WINDOW_DEFAULT_H  = 760

# ── PDF limits ─────────────────────────────────────────────────────────────────
PDF_MAX_PAGES = 20

# ── Ollama ─────────────────────────────────────────────────────────────────────
OLLAMA_TIMEOUT  = 300  # seconds — generous for slow CPU models (gemma3 etc.)
DEFAULT_MODEL   = "gemma2:2b"

# ── Zoom presets ───────────────────────────────────────────────────────────────
ZOOM_LEVELS = [50, 75, 100, 125, 150, 175, 200]
ZOOM_DEFAULT = 125
