#!/usr/bin/env python3
"""Tiny stdlib-only JSON API for the FCC router awareness database."""

from __future__ import annotations

import json
import sqlite3
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "fcc_router_consumer_awareness.db"

QUERIES = {
    "/api/status": "SELECT * FROM vw_current_consumer_status",
    "/api/faqs": "SELECT * FROM vw_public_faqs ORDER BY category, question",
    "/api/timeline": "SELECT * FROM vw_router_timeline ORDER BY event_date DESC",
    "/api/alerts": "SELECT severity, title, body, cta_label, cta_url FROM alerts WHERE active = 1 ORDER BY alert_id",
    "/api/sources": "SELECT * FROM vw_primary_sources ORDER BY publication_date DESC, source_key DESC",
}


def query_rows(sql: str, params: tuple[object, ...] = ()) -> list[dict[str, object]]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(sql, params)
        cols = [d[0] for d in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/healthz":
                payload: object = {"ok": True}
            elif parsed.path in QUERIES:
                payload = query_rows(QUERIES[parsed.path])
            elif parsed.path == "/api/search":
                q = parse_qs(parsed.query).get("q", [""])[0].strip()
                if not q:
                    self.respond({"error": "Missing q parameter"}, 400)
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
                payload = {"endpoints": ["/healthz", *sorted(QUERIES), "/api/search?q=firmware"]}
            self.respond(payload)
        except sqlite3.Error as exc:
            self.respond({"error": str(exc)}, 500)

    def respond(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    if not DB_PATH.exists():
        raise SystemExit(f"Database not found: {DB_PATH}")
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = HTTPServer(("localhost", port), Handler)
    print(f"Serving http://localhost:{port}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
