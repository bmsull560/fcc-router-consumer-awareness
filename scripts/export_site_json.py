#!/usr/bin/env python3
"""Export website-oriented JSON payloads from the SQLite database."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / 'data' / 'fcc_router_consumer_awareness.db'
DEFAULT_OUT = ROOT / 'site-data'

EXPORTS = {
    'current_status.json': 'SELECT * FROM vw_current_consumer_status',
    'timeline.json': 'SELECT * FROM vw_router_timeline ORDER BY event_date DESC',
    'faqs.json': 'SELECT * FROM vw_public_faqs ORDER BY category, question',
    'alerts.json': 'SELECT * FROM alerts WHERE active = 1 ORDER BY alert_id',
    'claims.json': 'SELECT * FROM claims ORDER BY claim_id',
    'conditional_approvals.json': 'SELECT * FROM vw_active_conditional_approvals ORDER BY approval_end_date, producer',
    'waivers.json': 'SELECT * FROM vw_active_waivers ORDER BY effective_end_date, party',
    'sources.json': 'SELECT * FROM vw_primary_sources ORDER BY publication_date DESC, source_key DESC',
    'search_index.json': '''
    SELECT
        table_name,
        row_id,
        title,
        snippet(search_index, 3, '<mark>', '</mark>', '...', 16) AS snippet
    FROM search_index
    ORDER BY table_name, row_id
    LIMIT 1000
''',
}


def rows_as_dicts(cursor: sqlite3.Cursor) -> list[dict[str, object]]:
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default=str(DEFAULT_OUT), help='output directory')
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        for filename, query in EXPORTS.items():
            data = rows_as_dicts(conn.execute(query))
            (out_dir / filename).write_text(
                json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + '\n',
                encoding='utf-8',
            )

    print(f'Exported {len(EXPORTS)} JSON files to {out_dir}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
