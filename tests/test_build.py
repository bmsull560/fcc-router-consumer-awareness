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

    def test_faq_page_contains_questions(self):
        from scripts.build_html import build_faqs
        html = build_faqs()
        self.assertIn('FAQs', html)

        site_data = ROOT / 'site-data'
        faqs = json.loads((site_data / 'faqs.json').read_text(encoding='utf-8'))
        if faqs:
            first = faqs[0]
            self.assertIn(first['question'], html)
            self.assertIn(first['category'], html)
            if first.get('source_urls'):
                first_url = first['source_urls'].split('|')[0].strip()
                self.assertIn(f'<a href="{first_url}">', html)

    def test_timeline_page_contains_events(self):
        from scripts.build_html import build_timeline
        html = build_timeline()
        self.assertIn('Timeline', html)

        events = json.loads((ROOT / 'site-data' / 'timeline.json').read_text(encoding='utf-8'))
        if events:
            self.assertIn(events[0]['title'], html)
            # Sorted by event_date descending; first rendered item matches max date.
            max_date = max(ev['event_date'] for ev in events)
            first_date_match = re.search(r'<h2>([^<]+)</h2>', html)
            if first_date_match:
                self.assertIn(max_date, first_date_match.group(1))
        # Count check: one card per event.
        self.assertEqual(len(re.findall(r'<article class="card">', html)), len(events))

    def test_waivers_page_contains_waivers(self):
        from scripts.build_html import build_waivers
        html = build_waivers()
        self.assertIn('Waivers', html)

        waivers = json.loads((ROOT / 'site-data' / 'waivers.json').read_text(encoding='utf-8'))
        if waivers:
            first = waivers[0]
            self.assertIn(first['party'], html)
            self.assertIn(first['equipment_scope'], html)
        # Count check: header row plus one data row per waiver.
        self.assertEqual(len(re.findall(r'<tr>', html)), len(waivers) + 1)

    def test_waivers_page_handles_null_dates(self):
        """Regression: null effective_start_date/effective_end_date render as empty/open-ended, not None."""
        from scripts import build_html
        original_load_json = build_html.load_json

        def patched_load_json(name):
            if name == 'waivers.json':
                return [{
                    'waiver_type': 'test_waiver',
                    'party': 'Test Party',
                    'equipment_scope': 'Test scope',
                    'effective_start_date': None,
                    'effective_end_date': None,
                    'source_url': 'https://example.com/',
                }]
            return original_load_json(name)

        build_html.load_json = patched_load_json
        try:
            html = build_html.build_waivers()
            self.assertIn('open-ended', html)
            self.assertNotIn('None', html)
        finally:
            build_html.load_json = original_load_json

    def test_approvals_page_contains_approvals(self):
        from scripts.build_html import build_approvals
        html = build_approvals()
        self.assertIn('Conditional Approvals', html)

        approvals = json.loads((ROOT / 'site-data' / 'conditional_approvals.json').read_text(encoding='utf-8'))
        if approvals:
            self.assertIn(approvals[0]['producer'], html)
        # Count check: header row plus one data row per approval.
        self.assertEqual(len(re.findall(r'<tr>', html)), len(approvals) + 1)

    def test_myths_page_contains_claims(self):
        from scripts.build_html import build_myths
        html = build_myths()
        self.assertIn('Myths', html)

        claims = json.loads((ROOT / 'site-data' / 'claims.json').read_text(encoding='utf-8'))
        if claims:
            self.assertIn(claims[0]['claim'], html)
            # mostly_true verdict uses a sanitized CSS class name.
            self.assertIn('verdict-mostly_true', html)
        # Count check: one card per claim.
        self.assertEqual(len(re.findall(r'<article class="card">', html)), len(claims))

    def test_sources_page_contains_sources(self):
        from scripts.build_html import build_sources
        html = build_sources()
        self.assertIn('Sources', html)

        sources = json.loads((ROOT / 'site-data' / 'sources.json').read_text(encoding='utf-8'))
        if sources:
            self.assertIn(sources[0]['title'], html)
        # Count check: one list item per source within the main body (nav also uses <li>).
        body_match = re.search(r'<main class="container">(.*)</main>', html, re.S)
        body = body_match.group(1) if body_match else html
        self.assertEqual(len(re.findall(r'<li>', body)), len(sources))

    def test_search_page_loads_index(self):
        from scripts.build_html import build_search
        html = build_search()
        self.assertIn('Search', html)
        self.assertIn('search_index.json', html)

    def test_css_class_sanitizes_values(self):
        from scripts.build_html import css_class
        self.assertEqual(css_class('WARNING!'), 'warning')
        self.assertEqual(css_class('urgent'), 'urgent')
        self.assertEqual(css_class('info notice'), 'infonotice')
        self.assertEqual(css_class('<script>'), 'script')

    def test_home_page_empty_states(self):
        from scripts import build_html
        original_load_json = build_html.load_json

        def empty_load_json(name):
            if name == 'current_status.json':
                return [{
                    'headline': 'Headline',
                    'continued_use_note': 'Note',
                    'update_note': 'Update',
                    'verification_note': 'Verify',
                    'current_as_of': '2026-07-09',
                }]
            return []

        build_html.load_json = empty_load_json
        try:
            html = build_html.build_home()
            self.assertIn('No active alerts.', html)
            self.assertIn('No FAQs available.', html)
            self.assertIn('No timeline events available.', html)
        finally:
            build_html.load_json = original_load_json

    def test_html_escaping(self):
        from scripts.build_html import e, render, Safe
        self.assertEqual(e('<script>'), '&lt;script&gt;')
        self.assertEqual(e('"quoted"'), '&quot;quoted&quot;')
        out = render('status.html', {
            'headline': '<script>alert(1)</script>',
            'continued_use_note': 'safe',
            'update_note': 'safe',
            'verification_note': 'safe',
            'alerts': Safe('<p>allowed html</p>'),
            'faqs': Safe(''),
            'timeline': Safe(''),
        })
        self.assertIn('&lt;script&gt;', out)
        self.assertIn('<p>allowed html</p>', out)

    def test_internal_links_resolve(self):
        import tempfile
        import subprocess
        import sys
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(
                [sys.executable, str(ROOT / 'scripts' / 'build_site.py'), '--out', tmp, '--site-data', str(ROOT / 'site-data')],
                check=True,
            )
            site = Path(tmp)
            html = (site / 'index.html').read_text(encoding='utf-8')
            hrefs = re.findall(r'href="([^"]+)"', html)
            for href in hrefs:
                if href.startswith('http') or href.startswith('#') or href.startswith('mailto:'):
                    continue
                parts = href.rstrip('/').split('/')
                candidate = site / Path(*parts)
                if href.endswith('/'):
                    candidate = candidate / 'index.html'
                self.assertTrue(candidate.exists(), f'Missing link target: {href}')
