import unittest
from pathlib import Path

from scripts.build_html import render_page


ROOT = Path(__file__).resolve().parents[1]


class TestBuildHtml(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import subprocess
        import sys
        subprocess.run([sys.executable, str(ROOT / 'scripts' / 'export_site_json.py')], check=True)

    def test_render_page_includes_title_and_body(self):
        out = render_page(title='Test', body='<p>Hello</p>')
        self.assertIn('<title>Test', out)
        self.assertIn('<p>Hello</p>', out)
        self.assertIn('Current as of', out)

    def test_title_is_escaped_and_body_is_safe(self):
        out = render_page(title='<script>alert(1)</script>', body='<p>Safe HTML</p>')
        self.assertIn('&lt;script&gt;', out)
        self.assertNotIn('<script>', out)
        self.assertIn('<p>Safe HTML</p>', out)
