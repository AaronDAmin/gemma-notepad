"""Data access layer — all SQL lives here, never in UI files."""
from __future__ import annotations
from datetime import datetime
from app.core.database import db
from app.core.models import Document, DocumentType


class DocumentRepository:

    def save(self, doc: Document) -> int:
        """Insert or update a document. Returns the row id."""
        with db.connect() as conn:
            if doc.id is None:
                cur = conn.execute(
                    """INSERT INTO documents
                       (workspace_id, name, doc_type, file_path, content,
                        page_count, current_page, zoom_level)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (doc.workspace_id, doc.name, doc.doc_type.value,
                     doc.file_path, doc.content, doc.page_count,
                     doc.current_page, doc.zoom_level),
                )
                return cur.lastrowid
            else:
                conn.execute(
                    """UPDATE documents SET name=?, doc_type=?, file_path=?,
                       content=?, page_count=?, current_page=?, zoom_level=?
                       WHERE id=?""",
                    (doc.name, doc.doc_type.value, doc.file_path,
                     doc.content, doc.page_count, doc.current_page,
                     doc.zoom_level, doc.id),
                )
                return doc.id

    def update_position(self, doc_id: int, page: int, zoom: int):
        with db.connect() as conn:
            conn.execute(
                "UPDATE documents SET current_page=?, zoom_level=? WHERE id=?",
                (page, zoom, doc_id),
            )

    def get_recent(self, limit: int = 10) -> list[Document]:
        with db.connect() as conn:
            rows = conn.execute(
                """SELECT * FROM documents
                   ORDER BY created_at DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        return [self._row_to_doc(r) for r in rows]

    def _row_to_doc(self, row) -> Document:
        return Document(
            id=row["id"],
            workspace_id=row["workspace_id"],
            name=row["name"],
            doc_type=DocumentType(row["doc_type"]),
            file_path=row["file_path"],
            content=row["content"],
            page_count=row["page_count"],
            current_page=row["current_page"],
            zoom_level=row["zoom_level"],
        )


class SettingsRepository:

    def get(self, key: str, default: str = "") -> str:
        with db.connect() as conn:
            row = conn.execute(
                "SELECT value FROM settings WHERE key=?", (key,)
            ).fetchone()
        return row["value"] if row else default

    def set(self, key: str, value: str):
        with db.connect() as conn:
            conn.execute(
                "INSERT INTO settings(key,value) VALUES(?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )


# Module-level singletons
doc_repo      = DocumentRepository()
settings_repo = SettingsRepository()
