#!/usr/bin/env python3
"""Tiny stdlib-only JSON API for the FCC router awareness database."""

from __future__ import annotations

import argparse
import json
import logging
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / 'data' / 'fcc_router_consumer_awareness.db'
DB_PATH: Path = DEFAULT_DB_PATH

DEFAULT_PORT = 8000
MAX_QUERY_LENGTH = 200

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
)
logger = logging.getLogger('sqlite_api')

QUERIES = {
    '/api/status': 'SELECT * FROM vw_current_consumer_status',
    '/api/faqs': 'SELECT * FROM vw_public_faqs ORDER BY category, question',
    '/api/timeline': 'SELECT * FROM vw_router_timeline ORDER BY event_date DESC',
    '/api/alerts': 'SELECT severity, title, body, cta_label, cta_url FROM alerts WHERE active = 1 ORDER BY alert_id',
    '/api/sources': 'SELECT * FROM vw_primary_sources ORDER BY publication_date DESC, source_key DESC',
}


def query_rows(sql: str, params: tuple[object, ...] = ()) -> list[dict[str, object]]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(sql, params)
        cols = [d[0] for d in cursor.description]
        return [dict(zip(cols, row, strict=True)) for row in cursor.fetchall()]


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        logger.info('%s %s', self.command, self.path)
        try:
            if parsed.path == '/healthz':
                payload: object = _health_check()
            elif parsed.path in QUERIES:
                payload = query_rows(QUERIES[parsed.path])
            elif parsed.path == '/api/search':
                q = parse_qs(parsed.query).get('q', [''])[0].strip()
                if not q:
                    self.respond({'error': 'Missing q parameter'}, 400)
                    return
                if len(q) > MAX_QUERY_LENGTH:
                    self.respond({'error': f'Query exceeds {MAX_QUERY_LENGTH} characters'}, 400)
                    return
                payload = query_rows(
                    """
                    SELECT table_name, row_id, title,
                           snippet(search_index, 3, '<mark>', '</mark>', '...', 16) AS snippet
                    FROM search_index
                    WHERE search_index MATCH ?
                    LIMIT 20
                    """,
                    (q,),
                )
            else:
                payload = {'endpoints': ['/healthz', *sorted(QUERIES), '/api/search?q=firmware']}
            self.respond(payload)
        except sqlite3.Error as exc:
            logger.exception('Database error serving %s', self.path)
            self.respond({'error': str(exc)}, 500)

    def respond(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload, indent=2, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Content-Security-Policy', "default-src 'none'")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        logger.info(format, *args)


def _health_check() -> dict[str, object]:
    """Return a health payload that confirms the database is reachable."""
    try:
        query_rows('SELECT 1')
        return {'ok': True, 'database': str(DB_PATH)}
    except sqlite3.Error as exc:
        logger.exception('Health check failed')
        return {'ok': False, 'error': str(exc)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Serve the FCC router awareness SQLite API.')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='TCP port to listen on')
    parser.add_argument('--db', default=str(DEFAULT_DB_PATH), help='path to SQLite database')
    args = parser.parse_args(argv)

    global DB_PATH
    db_path = Path(args.db)
    if not db_path.exists():
        raise SystemExit(f'Database not found: {db_path}')
    DB_PATH = db_path

    server = HTTPServer(('localhost', args.port), Handler)
    logger.info('Serving http://localhost:%d', args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info('Shutting down')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
