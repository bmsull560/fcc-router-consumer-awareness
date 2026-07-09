#!/usr/bin/env python3
"""Validate the FCC Router Consumer Awareness SQLite database."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / 'data' / 'fcc_router_consumer_awareness.db'

TABLES = [
    'sources', 'regulatory_events', 'covered_list_entries', 'definitions',
    'conditional_approvals', 'waivers', 'consumer_faqs', 'claims',
    'audience_segments', 'checklist_items', 'alerts', 'content_pages',
    'api_examples', 'update_jobs', 'data_notes',
]

VIEWS = [
    'vw_current_consumer_status',
    'vw_router_timeline',
    'vw_active_conditional_approvals',
    'vw_expiring_soon_conditional_approvals',
    'vw_active_waivers',
    'vw_public_faqs',
    'vw_primary_sources',
]


def count(conn: sqlite3.Connection, name: str) -> int:
    return int(conn.execute(f'SELECT COUNT(*) FROM {name}').fetchone()[0])


def main() -> int:
    if not DB_PATH.exists():
        raise SystemExit(f'Database not found: {DB_PATH}')

    with sqlite3.connect(DB_PATH) as conn:
        integrity = conn.execute('PRAGMA integrity_check').fetchone()[0]
        table_counts = {name: count(conn, name) for name in TABLES}
        view_counts = {name: count(conn, name) for name in VIEWS}
        fts5 = bool(conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='search_index'"
        ).fetchone())
        if fts5:
            conn.execute("SELECT COUNT(*) FROM search_index WHERE search_index MATCH 'router'").fetchone()

    payload = {
        'database': str(DB_PATH),
        'integrity_check': integrity,
        'table_counts': table_counts,
        'view_counts': view_counts,
        'fts5_search_index_present': fts5,
    }
    print(json.dumps(payload, indent=2))
    return 0 if integrity == 'ok' else 1


if __name__ == '__main__':
    raise SystemExit(main())
