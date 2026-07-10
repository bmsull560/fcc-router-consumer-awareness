"""Back up the SQLite database after an integrity check."""

from __future__ import annotations

import argparse
import gzip
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from app.config import get_settings


def _integrity_check(conn: sqlite3.Connection) -> None:
    cursor = conn.execute("PRAGMA integrity_check")
    result = cursor.fetchone()[0]
    if result != "ok":
        raise RuntimeError(f"Integrity check failed: {result}")


def backup_db(db_path: Path, backups_dir: Path, compress: bool = True) -> Path:
    """Copy the database to backups_dir with a timestamped name."""
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    backups_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    base_name = f"{db_path.stem}_{timestamp}"

    # Use the SQLite backup API for a consistent, transactional snapshot.
    src = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        _integrity_check(src)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir) / "backup.db"
            dst = sqlite3.connect(str(tmp_path))
            try:
                src.backup(dst)
            finally:
                dst.close()

            if compress:
                dest = backups_dir / f"{base_name}.db.gz"
                with gzip.open(dest, "wb") as out, open(tmp_path, "rb") as src_file:
                    out.write(src_file.read())
            else:
                dest = backups_dir / f"{base_name}.db"
                shutil.copy2(tmp_path, dest)
    finally:
        src.close()

    print(f"Backup created: {dest}")
    return dest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Back up the SQLite database")
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help="Path to the database (default: FCC_DB_PATH or project default)",
    )
    parser.add_argument(
        "--backups-dir",
        type=Path,
        default=Path("backups"),
        help="Directory to write backups to",
    )
    parser.add_argument(
        "--no-compress",
        action="store_true",
        help="Write an uncompressed copy instead of a .gz file",
    )
    args = parser.parse_args(argv)

    db_path = args.db_path or get_settings().db_path
    try:
        backup_db(db_path, args.backups_dir, compress=not args.no_compress)
    except Exception as exc:
        print(f"Backup failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
