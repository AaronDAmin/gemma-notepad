"""Icon helper for loading and rendering crisp SVG icons."""
from pathlib import Path
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QImage
from PySide6.QtCore import QSize, Qt
from PySide6.QtSvg import QSvgRenderer
from app.core.config import ICONS_DIR


def get_icon_path(name: str) -> Path:
    return ICONS_DIR / name


def load_svg_pixmap(name: str, size: int = 24, color: str | None = None) -> QPixmap:
    """Load an SVG icon as a crisp QPixmap at the given size."""
    path = get_icon_path(name)
    if not path.exists():
        return QPixmap()

    img = QImage(size, size, QImage.Format_ARGB32_Premultiplied)
    img.fill(Qt.transparent)

    renderer = QSvgRenderer(str(path))
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    renderer.render(p)

    if color:
        p.setCompositionMode(QPainter.CompositionMode_SourceIn)
        p.fillRect(img.rect(), QColor(color))

    p.end()
    return QPixmap.fromImage(img)


def load_svg_icon(name: str, size: int = 24, color: str | None = None) -> QIcon:
    """Load an SVG icon as a QIcon."""
    pix = load_svg_pixmap(name, size, color)
    return QIcon(pix)
