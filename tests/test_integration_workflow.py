"""Integration test for the database backup, restore, and validate workflow."""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from scripts.backup_db import backup_db
from scripts.restore_db import restore_db
from scripts.validate_db import validate


def test_backup_restore_validate_round_trip():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        try:
            conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY);")
            conn.execute("INSERT INTO t (id) VALUES (42);")
            conn.commit()
        finally:
            conn.close()

        backups_dir = tmp_path / "backups"
        backup_file = backup_db(db_path, backups_dir)
        assert backup_file.exists()

        restored_path = tmp_path / "restored.db"
        restore_db(backup_file, restored_path)

        result = validate(restored_path)
        assert result["integrity_check"] == "ok"

        conn = sqlite3.connect(str(restored_path))
        try:
            cursor = conn.execute("SELECT id FROM t")
            assert cursor.fetchone()[0] == 42
        finally:
            conn.close()
