"""Restore the SQLite database from a backup file."""

from __future__ import annotations

import argparse
import gzip
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

from app.config import get_settings


def _integrity_check(db_path: Path) -> None:
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    try:
        cursor = conn.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]
        if result != "ok":
            raise RuntimeError(f"Integrity check failed: {result}")
    finally:
        conn.close()


def restore_db(backup_path: Path, db_path: Path, *, force: bool = False) -> None:
    """Restore db_path from backup_path after verifying integrity."""
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup not found: {backup_path}")
    if db_path.exists() and not force:
        raise FileExistsError(
            f"Target database already exists: {db_path}. Use --force to overwrite."
        )

    # Decompress to a temporary file for integrity checking.
    suffix = ".db"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = Path(tmp.name)
        if backup_path.suffix == ".gz":
            with gzip.open(backup_path, "rb") as src:
                shutil.copyfileobj(src, tmp)  # type: ignore[misc]
        else:
            with open(backup_path, "rb") as src:
                shutil.copyfileobj(src, tmp)  # type: ignore[misc]

    try:
        _integrity_check(tmp_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(tmp_path), str(db_path))
        print(f"Restored {db_path} from {backup_path}")
    finally:
        tmp_path.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Restore the SQLite database from backup")
    parser.add_argument("backup", type=Path, help="Path to the backup file")
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help="Path to the database to restore (default: FCC_DB_PATH or project default)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the target database if it exists",
    )
    args = parser.parse_args(argv)

    db_path = args.db_path or get_settings().db_path
    try:
        restore_db(args.backup, db_path, force=args.force)
    except Exception as exc:
        print(f"Restore failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
