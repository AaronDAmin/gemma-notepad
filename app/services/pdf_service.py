"""PDF rendering and text extraction via PyMuPDF."""
from __future__ import annotations
import pymupdf as fitz  # PyMuPDF
from PySide6.QtGui import QPixmap, QImage
from app.core.config import PDF_MAX_PAGES


class PDFService:

    def open(self, path: str) -> fitz.Document:
        """Open a PDF. Raises ValueError if page count exceeds the limit."""
        doc = fitz.open(path)
        if doc.page_count > PDF_MAX_PAGES:
            doc.close()
            raise ValueError(
                f"This PDF has {doc.page_count} pages.\n"
                f"The maximum allowed is {PDF_MAX_PAGES} pages."
            )
        return doc

    def render_page(self, doc: fitz.Document, page_num: int,
                    zoom: float = 1.25) -> QPixmap:
        """Render a PDF page to a QPixmap at the given zoom level."""
        page   = doc[page_num]
        matrix = fitz.Matrix(zoom, zoom)
        pix    = page.get_pixmap(matrix=matrix, alpha=False)

        img = QImage(
            pix.samples, pix.width, pix.height,
            pix.stride, QImage.Format.Format_RGB888
        )
        return QPixmap.fromImage(img)

    def get_text_blocks(self, doc: fitz.Document,
                        page_num: int) -> list[dict]:
        """
        Return a list of text blocks for a page.
        Each block: {"text": str, "rect": fitz.Rect}
        Only blocks with actual text are returned.
        """
        page   = doc[page_num]
        blocks = page.get_text("blocks")   # (x0,y0,x1,y1,text,block_no,block_type)
        result = []
        for b in blocks:
            text = b[4].strip()
            if text and b[6] == 0:          # type 0 = text block
                result.append({"text": text, "rect": fitz.Rect(b[:4])})
        return result

    def get_context_around(self, doc: fitz.Document, page_num: int,
                            selected_text: str, n: int = 2) -> str:
        """
        Return up to n paragraphs before and after the paragraph
        containing selected_text, as a single context string.
        Falls back to the full page text if the paragraph isn't found.
        """
        blocks = self.get_text_blocks(doc, page_num)
        texts  = [b["text"] for b in blocks]

        # Find which block contains the selection
        idx = next(
            (i for i, t in enumerate(texts) if selected_text[:40] in t),
            None
        )
        if idx is None:
            # Fall back: entire page text
            return "\n\n".join(texts)

        start = max(0, idx - n)
        end   = min(len(texts), idx + n + 1)
        return "\n\n".join(texts[start:end])


# Module-level singleton
pdf_service = PDFService()
