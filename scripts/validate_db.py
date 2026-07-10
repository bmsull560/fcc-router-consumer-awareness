#!/usr/bin/env python3
"""Validate the FCC Router Consumer Awareness SQLite database."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "fcc_router_consumer_awareness.db"

TABLES = [
    "sources",
    "regulatory_events",
    "covered_list_entries",
    "definitions",
    "conditional_approvals",
    "waivers",
    "consumer_faqs",
    "claims",
    "audience_segments",
    "checklist_items",
    "alerts",
    "content_pages",
    "api_examples",
    "update_jobs",
    "data_notes",
]

VIEWS = [
    "vw_current_consumer_status",
    "vw_router_timeline",
    "vw_active_conditional_approvals",
    "vw_expiring_soon_conditional_approvals",
    "vw_active_waivers",
    "vw_public_faqs",
    "vw_primary_sources",
]

_KNOWN_NAMES = frozenset(TABLES) | frozenset(VIEWS)


def _count(conn: sqlite3.Connection, name: str) -> int:
    """Return the row count for a known table or view."""
    if name not in _KNOWN_NAMES:
        raise ValueError(f"Unknown table or view: {name}")
    return int(conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0])


def _safe_count(conn: sqlite3.Connection, name: str) -> int:
    """Return the row count for ``name``, or 0 if it does not exist."""
    try:
        return _count(conn, name)
    except sqlite3.OperationalError:
        return 0


def validate(db_path: Path) -> dict[str, object]:
    """Return validation results for the database at ``db_path``."""
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        integrity = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
    except sqlite3.DatabaseError as exc:
        if conn is not None:
            conn.close()
        raise ValueError(f"Not a valid SQLite database: {db_path}") from exc
    else:
        try:
            table_counts = {name: _safe_count(conn, name) for name in TABLES}
            view_counts = {name: _safe_count(conn, name) for name in VIEWS}
            fts5 = bool(
                conn.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='search_index'"
                ).fetchone()
            )
            fts5_match_count: int | None = None
            if fts5:
                fts5_match_count = int(
                    conn.execute(
                        "SELECT COUNT(*) FROM search_index WHERE search_index MATCH 'router'"
                    ).fetchone()[0]
                )
        finally:
            conn.close()

    return {
        "database": str(db_path),
        "integrity_check": integrity,
        "table_counts": table_counts,
        "view_counts": view_counts,
        "fts5_search_index_present": fts5,
        "fts5_match_count": fts5_match_count,
    }


def main() -> int:
    result = validate(DB_PATH)
    print(json.dumps(result, indent=2))
    return 0 if result["integrity_check"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
