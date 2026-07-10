"""SQLite migration runner."""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"


def _ensure_migrations_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            migration TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.commit()


def _get_applied_migrations(conn: sqlite3.Connection) -> set[str]:
    _ensure_migrations_table(conn)
    cursor = conn.execute("SELECT migration FROM schema_migrations")
    return {row[0] for row in cursor.fetchall()}


def _list_migration_files() -> list[Path]:
    if not MIGRATIONS_DIR.exists():
        return []
    return sorted(p for p in MIGRATIONS_DIR.iterdir() if p.suffix == ".sql")


def _is_existing_database(conn: sqlite3.Connection) -> bool:
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name != 'schema_migrations'"
    )
    return bool(cursor.fetchall())


def migrate(db_path: Path) -> int:
    """Apply pending migrations and return the number applied.

    Each migration is executed inside a single transaction managed by this
    runner. Migration files must not contain their own transaction-control
    statements (BEGIN, COMMIT, ROLLBACK) because they would conflict with the
    wrapper transaction.
    """
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        _ensure_migrations_table(conn)
        applied = _get_applied_migrations(conn)
        files = _list_migration_files()
        if not files:
            print("No migration files found.")
            return 0

        # Baseline: if the DB already has tables but no baseline record, mark it applied.
        baseline_file = files[0]
        baseline_name = baseline_file.name
        if baseline_name not in applied and _is_existing_database(conn):
            print(f"Baselining existing database with {baseline_name}")
            conn.execute(
                "INSERT INTO schema_migrations (migration) VALUES (?)",
                (baseline_name,),
            )
            conn.commit()
            applied.add(baseline_name)

        pending = [f for f in files if f.name not in applied]
        if not pending:
            print("Database is up to date.")
            return 0

        for migration_file in pending:
            sql = migration_file.read_text(encoding="utf-8")
            print(f"Applying {migration_file.name} ...")
            escaped_name = migration_file.name.replace("'", "''")
            transaction_sql = (
                "BEGIN;\n"
                f"{sql}\n"
                f"INSERT INTO schema_migrations (migration) VALUES ('{escaped_name}');\n"
                "COMMIT;"
            )
            try:
                conn.executescript(transaction_sql)
            except sqlite3.Error:
                conn.rollback()
                raise
        print(f"Applied {len(pending)} migration(s).")
        return len(pending)
    finally:
        conn.close()


def status(db_path: Path) -> None:
    """Print applied and pending migrations."""
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    try:
        applied = _get_applied_migrations(conn)
        files = _list_migration_files()
        print("Applied migrations:")
        for f in files:
            marker = "x" if f.name in applied else " "
            print(f"  [{marker}] {f.name}")
        pending = [f.name for f in files if f.name not in applied]
        if pending:
            print(f"Pending: {len(pending)}")
    finally:
        conn.close()


def create(name: str) -> Path:
    """Create a new numbered migration file."""
    MIGRATIONS_DIR.mkdir(parents=True, exist_ok=True)
    existing = _list_migration_files()
    next_num = 1
    if existing:
        last = existing[-1].stem
        match = re.match(r"^(\d+)", last)
        if match:
            next_num = int(match.group(1)) + 1
    filename = f"{next_num:04d}_{name}.sql"
    path = MIGRATIONS_DIR / filename
    path.write_text(f"-- Migration: {name}\n", encoding="utf-8")
    print(f"Created {path}")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SQLite migration runner")
    parser.add_argument(
        "--db-path",
        type=Path,
        default=Path("data") / "fcc_router_consumer_awareness.db",
        help="Path to the SQLite database",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("migrate", help="Apply pending migrations")
    subparsers.add_parser("status", help="Show migration status")
    create_parser = subparsers.add_parser("create", help="Create a new migration")
    create_parser.add_argument("name", help="Short descriptive name")

    args = parser.parse_args(argv)
    if args.command == "migrate":
        migrate(args.db_path)
        return 0
    if args.command == "status":
        status(args.db_path)
        return 0
    if args.command == "create":
        create(args.name)
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
