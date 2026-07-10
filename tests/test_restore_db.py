"""Tests for the database restore script."""

from __future__ import annotations

import gzip
import sqlite3

import pytest

from scripts.restore_db import restore_db


def test_restore_db_round_trip(tmp_path):
    original = tmp_path / "original.db"
    conn = sqlite3.connect(str(original))
    try:
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY);")
        conn.execute("INSERT INTO t (id) VALUES (42);")
        conn.commit()
    finally:
        conn.close()

    backup = tmp_path / "original_20240101_000000.db.gz"
    with open(original, "rb") as src, gzip.open(backup, "wb") as out:
        out.write(src.read())

    restored = tmp_path / "restored.db"
    restore_db(backup, restored)

    conn = sqlite3.connect(str(restored))
    try:
        cursor = conn.execute("SELECT id FROM t")
        assert cursor.fetchone()[0] == 42
    finally:
        conn.close()


def test_restore_db_refuses_overwrite_without_force(tmp_path):
    backup = tmp_path / "backup.db.gz"
    with gzip.open(backup, "wb") as out:
        out.write(b"SQLite format 3\x00" + b"\x00" * 100)
    existing = tmp_path / "existing.db"
    existing.write_bytes(b"not a db")
    with pytest.raises(FileExistsError):
        restore_db(backup, existing)


def test_restore_db_overwrites_with_force(tmp_path):
    original = tmp_path / "original.db"
    conn = sqlite3.connect(str(original))
    try:
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY);")
        conn.execute("INSERT INTO t (id) VALUES (42);")
        conn.commit()
    finally:
        conn.close()

    backup = tmp_path / "original_20240101_000000.db.gz"
    with open(original, "rb") as src, gzip.open(backup, "wb") as out:
        out.write(src.read())

    existing = tmp_path / "existing.db"
    existing.write_bytes(b"not a db")
    restore_db(backup, existing, force=True)

    conn = sqlite3.connect(str(existing))
    try:
        cursor = conn.execute("SELECT id FROM t")
        assert cursor.fetchone()[0] == 42
    finally:
        conn.close()


def test_main_restore_returns_zero(tmp_path):
    from scripts.restore_db import main

    original = tmp_path / "original.db"
    conn = sqlite3.connect(str(original))
    try:
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY);")
        conn.commit()
    finally:
        conn.close()

    backup = tmp_path / "original_20240101_000000.db.gz"
    with open(original, "rb") as src, gzip.open(backup, "wb") as out:
        out.write(src.read())

    restored = tmp_path / "restored.db"
    exit_code = main([str(backup), "--db-path", str(restored)])
    assert exit_code == 0
