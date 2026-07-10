import json
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from scripts.validate_db import TABLES, VIEWS, _count, main, validate

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "fcc_router_consumer_awareness.db"


def test_validate_real_database():
    result = validate(DB_PATH)
    assert result["integrity_check"] == "ok"
    assert result["database"] == str(DB_PATH)
    table_counts = result["table_counts"]
    view_counts = result["view_counts"]
    assert isinstance(table_counts, dict)
    assert isinstance(view_counts, dict)
    for table in TABLES:
        assert table in table_counts
        count = table_counts[table]
        assert isinstance(count, int)
        assert count >= 0
    for view in VIEWS:
        assert view in view_counts
        count = view_counts[view]
        assert isinstance(count, int)
        assert count >= 0
    assert result["fts5_search_index_present"] is True


def test_validate_missing_database():
    with tempfile.TemporaryDirectory() as tmp:
        missing = Path(tmp) / "missing.db"
        with pytest.raises(FileNotFoundError):
            validate(missing)


def test_validate_empty_database():
    with tempfile.TemporaryDirectory() as tmp:
        empty_db = Path(tmp) / "empty.db"
        sqlite3.connect(empty_db).close()
        result = validate(empty_db)
        assert result["integrity_check"] == "ok"
        table_counts = result["table_counts"]
        view_counts = result["view_counts"]
        assert isinstance(table_counts, dict)
        assert isinstance(view_counts, dict)
        assert all(count == 0 for count in table_counts.values())
        assert all(count == 0 for count in view_counts.values())
        assert result["fts5_search_index_present"] is False
        assert result["fts5_match_count"] is None


def test_cli_returns_zero_for_valid_database():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_db.py")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["integrity_check"] == "ok"


def test_validate_corrupt_database():
    with tempfile.TemporaryDirectory() as tmp:
        corrupt = Path(tmp) / "corrupt.db"
        corrupt.write_text("this is not a sqlite database", encoding="utf-8")
        with pytest.raises(ValueError):
            validate(corrupt)


def test_cli_returns_non_zero_for_failed_integrity():
    from scripts import validate_db

    original_validate = validate_db.validate

    def bad_validate(db_path: Path) -> dict[str, object]:
        return {
            "database": str(db_path),
            "integrity_check": "not ok",
            "table_counts": {},
            "view_counts": {},
            "fts5_search_index_present": False,
        }

    validate_db.validate = bad_validate
    try:
        assert main() == 1
    finally:
        validate_db.validate = original_validate


def test_count_rejects_unknown_identifier():
    conn = sqlite3.connect(":memory:")
    with pytest.raises(ValueError):
        _count(conn, "sources; DROP TABLE sources--")


def test_validate_real_database_exposes_fts5_match_count():
    result = validate(DB_PATH)
    assert result["fts5_search_index_present"] is True
    assert isinstance(result["fts5_match_count"], int)
    assert result["fts5_match_count"] >= 0
