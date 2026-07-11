"""Tests for the database validation script."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.validate_db import main as validate_db_main

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / 'data' / 'fcc_router_consumer_awareness.db'


class TestValidateDb(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not DB_PATH.exists():
            raise unittest.SkipTest(f'Database not found: {DB_PATH}')

    def test_validate_db_reports_integrity_ok(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / 'scripts' / 'validate_db.py')],
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload['integrity_check'], 'ok')
        self.assertFalse(payload['schema_errors'])
        self.assertFalse(payload['count_errors'])
        self.assertTrue(payload['fts5_search_index_present'])
        self.assertIn('table_counts', payload)
        self.assertIn('view_counts', payload)

    def test_validate_db_returns_nonzero_on_missing_db(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / 'missing.db'
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / 'scripts' / 'validate_db.py'),
                    '--db',
                    str(missing),
                ],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Database not found', result.stderr)

    def test_main_invocation_validates_database(self) -> None:
        returncode = validate_db_main(['--db', str(DB_PATH)])
        self.assertEqual(returncode, 0)


if __name__ == '__main__':
    raise SystemExit(unittest.main())
