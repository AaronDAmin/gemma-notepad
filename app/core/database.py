"""SQLite database manager — initialises the schema at startup."""
import sqlite3
from pathlib import Path
from app.core.config import DB_PATH


class DatabaseManager:
    def __init__(self, db_path: Path = DB_PATH):
        self._path = db_path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize(self):
        with self.connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS workspaces (
                    id   INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT    NOT NULL,
                    active_document_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS documents (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    workspace_id INTEGER REFERENCES workspaces(id) ON DELETE CASCADE,
                    name         TEXT    NOT NULL,
                    doc_type     TEXT    NOT NULL,
                    file_path    TEXT,
                    content      TEXT,
                    page_count   INTEGER DEFAULT 0,
                    current_page INTEGER DEFAULT 1,
                    zoom_level   INTEGER DEFAULT 125,
                    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS settings (
                    key   TEXT PRIMARY KEY,
                    value TEXT
                );
            """)
            # Ensure a default workspace exists (id=1)
            conn.execute(
                "INSERT OR IGNORE INTO workspaces(id, name) VALUES(1, 'Default')"
            )


# Module-level singleton
db = DatabaseManager()
