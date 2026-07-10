"""Tests for the database backup script."""

from __future__ import annotations

import gzip
import sqlite3

import pytest

from scripts.backup_db import backup_db


def test_backup_db_creates_compressed_backup(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY);")
        conn.commit()
    finally:
        conn.close()

    backups_dir = tmp_path / "backups"
    dest = backup_db(db_path, backups_dir)
    assert dest.exists()
    assert dest.suffixes == [".db", ".gz"]

    with gzip.open(dest, "rb") as f:
        header = f.read(16)
    assert header.startswith(b"SQLite format 3")


def test_backup_db_requires_existing_database(tmp_path):
    backups_dir = tmp_path / "backups"
    with pytest.raises(FileNotFoundError):
        backup_db(tmp_path / "missing.db", backups_dir)


def test_backup_db_uncompressed(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY);")
        conn.commit()
    finally:
        conn.close()

    backups_dir = tmp_path / "backups"
    dest = backup_db(db_path, backups_dir, compress=False)
    assert dest.exists()
    assert dest.suffix == ".db"
    with open(dest, "rb") as f:
        assert f.read(16).startswith(b"SQLite format 3")


def test_main_backup_returns_zero(tmp_path):
    from scripts.backup_db import main

    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY);")
        conn.commit()
    finally:
        conn.close()

    backups_dir = tmp_path / "backups"
    exit_code = main(["--db-path", str(db_path), "--backups-dir", str(backups_dir)])
    assert exit_code == 0
    assert any(backups_dir.iterdir())
