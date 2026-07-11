import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.build_site import main as build_site_main

ROOT = Path(__file__).resolve().parents[1]


class TestBuildSite(unittest.TestCase):
    def test_build_site_creates_all_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(ROOT / 'scripts' / 'build_site.py'), '--out', tmp],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            out = Path(tmp)
            self.assertTrue((out / 'index.html').exists())
            self.assertTrue((out / 'index.html').stat().st_size > 0)
            self.assertTrue((out / 'faqs' / 'index.html').exists())
            self.assertTrue((out / 'timeline' / 'index.html').exists())
            self.assertTrue((out / 'waivers' / 'index.html').exists())
            self.assertTrue((out / 'approvals' / 'index.html').exists())
            self.assertTrue((out / 'myths' / 'index.html').exists())
            self.assertTrue((out / 'sources' / 'index.html').exists())
            self.assertTrue((out / 'search' / 'index.html').exists())
            self.assertIn(
                'search_index.json', (out / 'search' / 'index.html').read_text(encoding='utf-8')
            )
            self.assertTrue((out / 'static' / 'style.css').exists())
            self.assertTrue((out / 'search' / 'search_index.json').exists())

            index = (out / 'index.html').read_text(encoding='utf-8')
            self.assertIn('FCC Router Consumer Awareness', index)
            self.assertIn('Current as of', index)
            self.assertIn('<link rel="stylesheet" href="static/style.css">', index)

    def test_build_site_default_output_preserves_static_source(self) -> None:
        """Default build writes to site/ without deleting the tracked source in site/static/."""
        result = subprocess.run(
            [sys.executable, str(ROOT / 'scripts' / 'build_site.py')],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((ROOT / 'site' / 'index.html').exists())
        self.assertTrue((ROOT / 'site' / 'static' / 'style.css').exists())
        self.assertTrue((ROOT / 'site' / 'static' / 'search.js').exists())
        self.assertTrue((ROOT / 'site' / 'search' / 'search_index.json').exists())

    def test_build_site_main_invocation_creates_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_dir = Path(tmp) / 'site'
            build_site_main(['--out', str(site_dir), '--site-data', str(ROOT / 'site-data')])
            self.assertTrue((site_dir / 'index.html').exists())
            self.assertTrue((site_dir / 'faqs' / 'index.html').exists())
            self.assertTrue((site_dir / 'search' / 'search_index.json').exists())


if __name__ == '__main__':
    raise SystemExit(unittest.main())
