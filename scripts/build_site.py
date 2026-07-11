#!/usr/bin/env python3
"""Top-level orchestrator: export JSON from SQLite, then render static HTML."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_SUBPROCESS_ENV = os.environ.copy()
_SUBPROCESS_ENV['PYTHONPATH'] = str(ROOT) + os.pathsep + _SUBPROCESS_ENV.get('PYTHONPATH', '')


def run_export(out_dir: Path) -> None:
    """Export SQLite data to JSON in out_dir."""
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(ROOT / 'scripts' / 'export_site_json.py'), '--out', str(out_dir)],
        capture_output=True,
        text=True,
        timeout=120,
        env=_SUBPROCESS_ENV,
    )
    if result.returncode != 0:
        raise SystemExit(f'Export failed:\nstdout: {result.stdout}\nstderr: {result.stderr}')
    print(result.stdout.strip())


def run_build(site_data_dir: Path, site_dir: Path) -> None:
    """Render static HTML pages from site-data JSON into site_dir."""
    result = subprocess.run(  # noqa: S603
        [
            sys.executable,
            str(ROOT / 'scripts' / 'build_html.py'),
            '--site-data',
            str(site_data_dir),
            '--site',
            str(site_dir),
        ],
        capture_output=True,
        text=True,
        timeout=120,
        env=_SUBPROCESS_ENV,
    )
    if result.returncode != 0:
        raise SystemExit(f'Build failed:\nstdout: {result.stdout}\nstderr: {result.stderr}')
    print(result.stdout.strip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Build the static FCC router awareness website.')
    parser.add_argument('--out', default=str(ROOT / 'site'), help='output directory for HTML site')
    parser.add_argument(
        '--site-data', default=str(ROOT / 'site-data'), help='intermediate JSON directory'
    )
    args = parser.parse_args(argv)

    site_data_dir = Path(args.site_data)
    site_dir = Path(args.out)

    run_export(site_data_dir)
    run_build(site_data_dir, site_dir)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
