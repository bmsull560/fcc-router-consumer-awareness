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

    def test_home_page_contains_status_and_alerts(self):
        import json
        from scripts.build_html import build_home
        html = build_home()
        self.assertIn('FCC Router Consumer Awareness', html)
        self.assertIn('Current as of', html)

        site_data = ROOT / 'site-data'
        status = json.loads((site_data / 'current_status.json').read_text(encoding='utf-8'))
        if status:
            status = status[0]
            self.assertIn(status.get('headline', ''), html)
        alerts = json.loads((site_data / 'alerts.json').read_text(encoding='utf-8'))
        if alerts:
            self.assertIn(alerts[0].get('title', ''), html)
        faqs = json.loads((site_data / 'faqs.json').read_text(encoding='utf-8'))
        if faqs:
            self.assertIn(faqs[0].get('question', ''), html)
        timeline = json.loads((site_data / 'timeline.json').read_text(encoding='utf-8'))
        if timeline:
            self.assertIn(timeline[0].get('title', ''), html)
