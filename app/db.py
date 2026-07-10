"""SQLite database dependency for FastAPI."""

from __future__ import annotations

import sqlite3
from collections.abc import Generator

from app.config import get_settings


def get_db_conn() -> Generator[sqlite3.Connection, None, None]:
    """Yield a SQLite connection and close it after the request."""
    settings = get_settings()
    conn = sqlite3.connect(str(settings.db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
