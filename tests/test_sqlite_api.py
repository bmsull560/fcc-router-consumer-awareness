"""Tests for the tiny SQLite JSON API server."""

from __future__ import annotations

import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import HTTPServer
from pathlib import Path

from app.sqlite_api import DB_PATH, Handler

ROOT = Path(__file__).resolve().parents[1]


class TestSqliteApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not DB_PATH.exists():
            raise unittest.SkipTest(f'Database not found: {DB_PATH}')

    def _request(self, url: str, timeout: float = 5.0) -> tuple[int, object]:
        """Make a GET request and return (status, parsed JSON)."""
        with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310
            status = response.status
            payload = json.loads(response.read().decode('utf-8'))
            return status, payload

    def test_healthz_returns_ok_and_database_path(self) -> None:
        server, port = self._start_server()
        try:
            status, payload = self._request(f'http://localhost:{port}/healthz')
            self.assertEqual(status, 200)
            self.assertIsInstance(payload, dict)
            assert isinstance(payload, dict)
            self.assertTrue(payload.get('ok'))
            self.assertIn('database', payload)
        finally:
            server.shutdown()

    def test_response_includes_security_headers(self) -> None:
        server, port = self._start_server()
        try:
            with urllib.request.urlopen(
                f'http://localhost:{port}/healthz', timeout=5.0
            ) as response:  # noqa: S310
                self.assertEqual(response.status, 200)
                self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')
                self.assertEqual(response.headers.get('X-Frame-Options'), 'DENY')
                self.assertIn(
                    "default-src 'none'", response.headers.get('Content-Security-Policy', '')
                )
        finally:
            server.shutdown()

    def test_search_rejects_overly_long_query(self) -> None:
        server, port = self._start_server()
        try:
            with self.assertRaises(urllib.error.HTTPError) as cm:
                self._request(f'http://localhost:{port}/api/search?q={"x" * 500}')
            self.assertEqual(cm.exception.code, 400)
        finally:
            server.shutdown()

    def test_status_endpoint_returns_list(self) -> None:
        server, port = self._start_server()
        try:
            status, payload = self._request(f'http://localhost:{port}/api/status')
            self.assertEqual(status, 200)
            self.assertIsInstance(payload, list)
            assert isinstance(payload, list)
            if payload:
                self.assertIn('headline', payload[0])
        finally:
            server.shutdown()

    def test_search_requires_q_parameter(self) -> None:
        server, port = self._start_server()
        try:
            with self.assertRaises(urllib.error.HTTPError) as cm:
                urllib.request.urlopen(  # noqa: S310
                    f'http://localhost:{port}/api/search', timeout=5.0
                )
            self.assertEqual(cm.exception.code, 400)
        finally:
            server.shutdown()

    def test_search_with_q_returns_results(self) -> None:
        server, port = self._start_server()
        try:
            status, payload = self._request(f'http://localhost:{port}/api/search?q=firmware')
            self.assertEqual(status, 200)
            self.assertIsInstance(payload, list)
        finally:
            server.shutdown()

    def test_unknown_path_returns_endpoint_index(self) -> None:
        server, port = self._start_server()
        try:
            status, payload = self._request(f'http://localhost:{port}/not-a-path')
            self.assertEqual(status, 200)
            self.assertIsInstance(payload, dict)
            assert isinstance(payload, dict)
            self.assertIn('endpoints', payload)
            self.assertIn('/healthz', payload['endpoints'])
        finally:
            server.shutdown()

    def test_status_endpoint_returns_500_on_db_error(self) -> None:
        import app.sqlite_api as sqlite_api

        original_db_path = sqlite_api.DB_PATH
        sqlite_api.DB_PATH = Path('/nonexistent/database.db')
        try:
            server, port = self._start_server()
            try:
                with self.assertRaises(urllib.error.HTTPError) as cm:
                    self._request(f'http://localhost:{port}/api/status')
                exc = cm.exception
                self.assertEqual(exc.code, 500)
                payload = json.loads(exc.read().decode('utf-8'))
                self.assertIn('error', payload)
            finally:
                server.shutdown()
        finally:
            sqlite_api.DB_PATH = original_db_path

    def _start_server(self) -> tuple[HTTPServer, int]:
        """Start the API server on an ephemeral port and return it."""
        server = HTTPServer(('localhost', 0), Handler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, port


if __name__ == '__main__':
    raise SystemExit(unittest.main())
