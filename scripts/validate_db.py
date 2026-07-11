#!/usr/bin/env python3
"""Validate the FCC Router Consumer Awareness SQLite database."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / 'data' / 'fcc_router_consumer_awareness.db'

TABLES = [
    'sources',
    'regulatory_events',
    'covered_list_entries',
    'definitions',
    'conditional_approvals',
    'waivers',
    'consumer_faqs',
    'claims',
    'audience_segments',
    'checklist_items',
    'alerts',
    'content_pages',
    'api_examples',
    'update_jobs',
    'data_notes',
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

# Minimum expected row counts for a non-empty dataset.
MIN_TABLE_COUNTS: dict[str, int] = {
    'sources': 1,
    'regulatory_events': 1,
    'conditional_approvals': 1,
    'waivers': 1,
    'consumer_faqs': 1,
    'claims': 1,
    'alerts': 1,
}

MIN_VIEW_COUNTS: dict[str, int] = {
    'vw_current_consumer_status': 1,
    'vw_router_timeline': 1,
    'vw_active_conditional_approvals': 1,
    'vw_active_waivers': 1,
    'vw_public_faqs': 1,
    'vw_primary_sources': 1,
}


def count(conn: sqlite3.Connection, name: str) -> int:
    if name not in TABLES and name not in VIEWS:
        raise ValueError(f'Untrusted relation name: {name}')
    return int(conn.execute(f'SELECT COUNT(*) FROM {name}').fetchone()[0])  # noqa: S608


def _schema_errors(conn: sqlite3.Connection) -> list[str]:
    """Return human-readable schema errors if expected tables/views are missing."""
    errors = []
    present = {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view')")
    }
    for name in TABLES:
        if name not in present:
            errors.append(f'Missing table: {name}')
    for name in VIEWS:
        if name not in present:
            errors.append(f'Missing view: {name}')
    return errors


def _count_errors(table_counts: dict[str, int], view_counts: dict[str, int]) -> list[str]:
    """Return errors for tables or views with fewer rows than expected."""
    errors = []
    for name, minimum in MIN_TABLE_COUNTS.items():
        if table_counts.get(name, 0) < minimum:
            errors.append(
                f'Table {name} has {table_counts.get(name, 0)} rows (expected >= {minimum})'
            )
    for name, minimum in MIN_VIEW_COUNTS.items():
        if view_counts.get(name, 0) < minimum:
            errors.append(
                f'View {name} has {view_counts.get(name, 0)} rows (expected >= {minimum})'
            )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Validate the FCC Router Consumer Awareness SQLite database.'
    )
    parser.add_argument('--db', default=str(DEFAULT_DB_PATH), help='path to SQLite database')
    args = parser.parse_args(argv)

    db_path = Path(args.db)
    if not db_path.exists():
        print(json.dumps({'error': f'Database not found: {db_path}'}), file=sys.stderr)
        return 1

    with sqlite3.connect(db_path) as conn:
        integrity = conn.execute('PRAGMA integrity_check').fetchone()[0]
        schema_errors = _schema_errors(conn)
        table_counts = {name: count(conn, name) for name in TABLES}
        view_counts = {name: count(conn, name) for name in VIEWS}
        count_errors = _count_errors(table_counts, view_counts)
        fts5 = bool(
            conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='search_index'"
            ).fetchone()
        )
        if fts5:
            conn.execute(
                "SELECT COUNT(*) FROM search_index WHERE search_index MATCH 'router'"
            ).fetchone()

    payload = {
        'database': str(db_path),
        'integrity_check': integrity,
        'schema_errors': schema_errors,
        'count_errors': count_errors,
        'table_counts': table_counts,
        'view_counts': view_counts,
        'fts5_search_index_present': fts5,
    }
    print(json.dumps(payload, indent=2))
    ok = integrity == 'ok' and not schema_errors and not count_errors
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
