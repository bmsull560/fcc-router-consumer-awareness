#!/usr/bin/env python3
"""Top-level orchestrator: export JSON from SQLite, then render static HTML."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_export(out_dir: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / 'scripts' / 'export_site_json.py'), '--out', str(out_dir)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(f'Export failed: {result.stderr}')
    print(result.stdout.strip())


def run_build(site_data_dir: Path, site_dir: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / 'scripts' / 'build_html.py'), '--site-data', str(site_data_dir), '--site', str(site_dir)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(f'Build failed: {result.stderr}')
    print(result.stdout.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description='Build the static FCC router awareness website.')
    parser.add_argument('--out', default=str(ROOT / 'site'), help='output directory for HTML site')
    parser.add_argument('--site-data', default=str(ROOT / 'site-data'), help='intermediate JSON directory')
    args = parser.parse_args()

    site_data_dir = Path(args.site_data)
    site_dir = Path(args.out)

    run_export(site_data_dir)
    run_build(site_data_dir, site_dir)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
