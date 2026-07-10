"""Tests for the SQLite migration runner."""

from __future__ import annotations

import sqlite3

import pytest

from scripts.migrate import create, migrate


@pytest.fixture
def tmp_migrations_dir(monkeypatch, tmp_path):
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir()
    monkeypatch.setattr(
        "scripts.migrate.MIGRATIONS_DIR",
        migrations_dir,
    )
    return migrations_dir


def test_migrate_applies_baseline_on_empty_db(tmp_migrations_dir, tmp_path):
    baseline = tmp_migrations_dir / "0001_baseline.sql"
    baseline.write_text("CREATE TABLE t (id INTEGER PRIMARY KEY);", encoding="utf-8")

    db_path = tmp_path / "test.db"
    applied = migrate(db_path)
    assert applied == 1

    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        assert "t" in tables
        assert "schema_migrations" in tables
    finally:
        conn.close()


def test_migrate_baselines_existing_db(tmp_migrations_dir, tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("CREATE TABLE existing (id INTEGER PRIMARY KEY);")
        conn.commit()
    finally:
        conn.close()

    baseline = tmp_migrations_dir / "0001_baseline.sql"
    baseline.write_text("CREATE TABLE t (id INTEGER PRIMARY KEY);", encoding="utf-8")

    applied = migrate(db_path)
    assert applied == 0  # baseline is recorded, not re-executed

    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.execute("SELECT migration FROM schema_migrations")
        assert cursor.fetchone()[0] == "0001_baseline.sql"
    finally:
        conn.close()


def test_migrate_applies_only_pending(tmp_migrations_dir, tmp_path):
    baseline = tmp_migrations_dir / "0001_baseline.sql"
    baseline.write_text("CREATE TABLE t (id INTEGER PRIMARY KEY);", encoding="utf-8")
    follow_up = tmp_migrations_dir / "0002_add_col.sql"
    follow_up.write_text("ALTER TABLE t ADD COLUMN name TEXT;", encoding="utf-8")

    db_path = tmp_path / "test.db"
    applied = migrate(db_path)
    assert applied == 2

    applied2 = migrate(db_path)
    assert applied2 == 0


def test_create_migration(tmp_migrations_dir, tmp_path):
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr("scripts.migrate.MIGRATIONS_DIR", tmp_migrations_dir)
    path = create("add_sources_index")
    assert path.exists()
    assert path.name == "0001_add_sources_index.sql"
    monkeypatch.undo()


def test_migrate_is_atomic_on_failure(tmp_migrations_dir, tmp_path):
    baseline = tmp_migrations_dir / "0001_baseline.sql"
    baseline.write_text("CREATE TABLE t (id INTEGER PRIMARY KEY);", encoding="utf-8")
    bad = tmp_migrations_dir / "0002_bad.sql"
    bad.write_text("ALTER TABLE t ADD COLUMN name TEXT; THIS IS INVALID SQL;", encoding="utf-8")

    db_path = tmp_path / "test.db"
    with pytest.raises(sqlite3.Error):
        migrate(db_path)

    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.execute("PRAGMA table_info(t)")
        columns = {row[1] for row in cursor.fetchall()}
        assert "name" not in columns
        cursor = conn.execute("SELECT migration FROM schema_migrations")
        assert cursor.fetchone()[0] == "0001_baseline.sql"
    finally:
        conn.close()


def test_main_migrate_returns_zero(tmp_migrations_dir, tmp_path, monkeypatch):
    monkeypatch.setattr("scripts.migrate.MIGRATIONS_DIR", tmp_migrations_dir)
    baseline = tmp_migrations_dir / "0001_baseline.sql"
    baseline.write_text("CREATE TABLE t (id INTEGER PRIMARY KEY);", encoding="utf-8")

    from scripts.migrate import main

    db_path = tmp_path / "test.db"
    exit_code = main(["--db-path", str(db_path), "migrate"])
    assert exit_code == 0
