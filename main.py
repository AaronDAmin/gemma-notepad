"""
GemmaNotepad1 — entry point.

Usage:
    python main.py
"""
import sys
from pathlib import Path

# ── Make sure the project root is on sys.path ──────────────────────────────────
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QDir
from PySide6.QtGui import QFontDatabase, QFont, QIcon

from app.core.config  import STYLES_DIR, APP_NAME
from app.ui.main_window import MainWindow


def load_stylesheet(app: QApplication) -> None:
    """Load the global QSS theme."""
    qss_path = STYLES_DIR / "theme.qss"
    if qss_path.exists():
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    else:
        print(f"[warn] theme.qss not found at {qss_path}")


def configure_app(app: QApplication) -> None:
    """Set application-wide properties."""
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("GemmaNotepad1Study")

    # High-DPI support (AA_UseHighDpiPixmaps is deprecated in Qt 6 — built-in by default)

    # Prefer a clean system font
    preferred_fonts = ["Segoe UI", "Inter", "Helvetica Neue", "Arial"]
    for font_name in preferred_fonts:
        font = QFont(font_name, 10)
        if font.exactMatch() or font_name == preferred_fonts[-1]:
            app.setFont(font)
            break


def main() -> int:
    app = QApplication(sys.argv)
    configure_app(app)
    load_stylesheet(app)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
