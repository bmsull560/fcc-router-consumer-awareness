import json
import re
import unittest
from pathlib import Path

from scripts.build_html import HOME_PREVIEW_LIMIT, build_home, render_page


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

    def test_home_page_contains_status_alerts_faqs_and_timeline(self):
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

        # Verify preview limits within each section.
        faq_section = re.search(r'Top questions(.*?)Latest timeline events', html, re.S)
        self.assertIsNotNone(faq_section)
        faq_cards = re.findall(r'<article class="card">', faq_section.group(1))
        self.assertLessEqual(len(faq_cards), HOME_PREVIEW_LIMIT)

        timeline_section = re.search(r'Latest timeline events(.*)', html, re.S)
        self.assertIsNotNone(timeline_section)
        timeline_items = re.findall(r'<li>', timeline_section.group(1))
        self.assertLessEqual(len(timeline_items), HOME_PREVIEW_LIMIT)

        # Verify timeline is sorted by descending event_date.
        first_date_match = re.search(r'<li><strong>([^<]+)</strong>', timeline_section.group(1))
        if first_date_match and timeline:
            max_date = max(ev['event_date'] for ev in timeline)
            self.assertEqual(first_date_match.group(1), max_date)
