#!/usr/bin/env python3
"""Render static HTML pages from site-data JSON using stdlib templates."""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parents[1]
SITE_DATA_DIR = ROOT / 'site-data'
SITE_DIR = ROOT / 'site'
TEMPLATE_DIR = ROOT / 'site' / 'templates'
STATIC_DIR = ROOT / 'site' / 'static'

HOME_PREVIEW_LIMIT = 3


def load_json(name: str) -> list[dict[str, object]] | dict[str, object]:
    path = SITE_DATA_DIR / name
    return json.loads(path.read_text(encoding='utf-8'))


def e(value: object) -> str:
    """HTML-escape a value."""
    return html.escape(str(value), quote=True)


_CSS_CLASS_RE = re.compile(r'[^a-z0-9_-]')


def css_class(value: object) -> str:
    """Sanitize a value for use as a CSS class name."""
    return _CSS_CLASS_RE.sub('', str(value).lower())


class Safe:
    """Wrapper for pre-escaped HTML that should not be double-escaped."""
    def __init__(self, markup: str):
        self.html = markup

    def __str__(self) -> str:
        return self.html


def render(template_name: str, mapping: dict[str, object]) -> str:
    template_text = (TEMPLATE_DIR / template_name).read_text(encoding='utf-8')
    safe = {}
    for k, v in mapping.items():
        if isinstance(v, Safe):
            safe[k] = v.html
        elif isinstance(v, (str, int, float, bool)):
            safe[k] = e(v)
        else:
            raise TypeError(
                f"Template value for {k!r} must be str, Safe, or scalar; "
                f"got {type(v).__name__}"
            )
    return Template(template_text).substitute(safe)


def render_page(title: str, body: str, current_as_of: str = '2026-07-09', root: str = '') -> str:
    return render(
        'base.html',
        {
            'title': title,
            'body': Safe(body),
            'current_as_of': current_as_of,
            'root': root,
        },
    )


def build_home(root: str = '') -> str:
    """Render the home page from site-data JSON."""
    statuses = load_json('current_status.json')
    if isinstance(statuses, dict):
        statuses = [statuses]
    status = statuses[0] if statuses else {}
    alerts = load_json('alerts.json')
    faqs = load_json('faqs.json')
    timeline = load_json('timeline.json')

    alerts_html = ''.join(
        f'<div class="alert alert-{css_class(a["severity"])}"><strong>{e(a["title"])}</strong><p>{e(a["body"])}</p></div>'
        for a in alerts
    ) if alerts else '<p>No active alerts.</p>'

    faqs_html = ''.join(
        f'<article class="card"><h3>{e(f["question"])}</h3><p>{e(f["answer_short"])}</p></article>'
        for f in faqs[:HOME_PREVIEW_LIMIT]
    ) if faqs else '<p>No FAQs available.</p>'

    timeline_sorted = sorted(timeline, key=lambda ev: ev['event_date'], reverse=True)
    timeline_html = '<ul>' + ''.join(
        f'<li><strong>{e(ev["event_date"])}</strong> — {e(ev["title"])}<br>{e(ev["summary"])}</li>'
        for ev in timeline_sorted[:HOME_PREVIEW_LIMIT]
    ) + '</ul>' if timeline else '<p>No timeline events available.</p>'

    body = render(
        'status.html',
        {
            'headline': status.get('headline', ''),
            'continued_use_note': status.get('continued_use_note', ''),
            'update_note': status.get('update_note', ''),
            'verification_note': status.get('verification_note', ''),
            'alerts': Safe(alerts_html),
            'faqs': Safe(faqs_html),
            'timeline': Safe(timeline_html),
        },
    )
    return render_page(title='Home', body=body, current_as_of=status.get('current_as_of', '2026-07-09'), root=root)


def source_links(urls: str) -> str:
    """Turn a pipe-separated list of source URLs into HTML links."""
    if not urls:
        return ''
    parts = [u.strip() for u in str(urls).split('|') if u.strip()]
    return ' | '.join(f'<a href="{e(u)}">{e(u)}</a>' for u in parts)


def build_faqs(root: str = '') -> str:
    """Render the FAQ page from site-data JSON, grouped by category."""
    faqs = load_json('faqs.json')
    if not faqs:
        body = render('faqs.html', {'faq_groups': Safe('<p>No FAQs available.</p>')})
        return render_page(title='FAQs', body=body, root=root)

    by_category: dict[str, list[dict[str, object]]] = {}
    for f in faqs:
        by_category.setdefault(f['category'], []).append(f)

    groups = []
    for category, items in sorted(by_category.items()):
        items_html = ''.join(
            f'<article class="card"><h3>{e(item["question"])}</h3>'
            f'<p><strong>Short answer:</strong> {e(item["answer_short"])}</p>'
            f'<p>{e(item["answer_long"])}</p>'
            f'{_faq_sources_html(item.get("source_urls", ""))}</article>'
            for item in items
        )
        groups.append(f'<h2>{e(category)}</h2>{items_html}')

    body = render('faqs.html', {'faq_groups': Safe(''.join(groups))})
    return render_page(title='FAQs', body=body, root=root)


def _faq_sources_html(urls: str) -> str:
    """Return the rendered Sources line for an FAQ card, or empty string if none."""
    sources = source_links(urls)
    if not sources:
        return ''
    return f'<p class="source-link">Sources: {sources}</p>'


def build_timeline(root: str = '') -> str:
    """Render the regulatory timeline page."""
    events = load_json('timeline.json')
    if not events:
        events_html = '<p>No timeline events available.</p>'
    else:
        events_sorted = sorted(events, key=lambda ev: ev['event_date'], reverse=True)
        events_html = ''.join(
            f'<article class="card"><h2>{e(ev["event_date"])} — {e(ev["title"])}</h2>'
            f'<p><span class="label">Type:</span> {e(ev["event_type"])}</p>'
            f'<p>{e(ev["summary"])}</p>'
            f'<p><strong>Consumer impact:</strong> {e(ev.get("consumer_impact", ""))}</p>'
            f'<p class="source-link"><a href="{e(ev["source_url"])}">Source: {e(ev["source_title"])}</a></p></article>'
            for ev in events_sorted
        )
    return render_page(title='Timeline', body=render('timeline.html', {'events': Safe(events_html)}), root=root)


def build_waivers(root: str = '') -> str:
    """Render the active waivers page."""
    waivers = load_json('waivers.json')
    if not waivers:
        table = '<p>No waivers available.</p>'
    else:
        rows = []
        for w in waivers:
            start = w.get("effective_start_date") or ""
            end = w.get("effective_end_date") or "open-ended"
            rows.append(
                f'<tr><td>{e(w["waiver_type"])}</td><td>{e(w["party"])}</td>'
                f'<td>{e(w["equipment_scope"])}</td><td>{e(start)}</td>'
                f'<td>{e(end)}</td>'
                f'<td><a href="{e(w["source_url"])}">source</a></td></tr>'
            )
        rows = ''.join(rows)
        table = f'<table><thead><tr><th>Type</th><th>Party</th><th>Scope</th><th>Start</th><th>End</th><th>Source</th></tr></thead><tbody>{rows}</tbody></table>'
    return render_page(title='Waivers', body=render('waivers.html', {'waiver_table': Safe(table)}), root=root)


def build_approvals(root: str = '') -> str:
    """Render the conditional approvals page."""
    approvals = load_json('conditional_approvals.json')
    if not approvals:
        table = '<p>No conditional approvals available.</p>'
    else:
        rows = []
        for a in approvals:
            start = a.get("approval_start_date") or ""
            end = a.get("approval_end_date") or "open-ended"
            rows.append(
                f'<tr><td>{e(a["producer"])}</td><td>{e(a.get("brand_or_product_family", ""))}</td>'
                f'<td>{e(a["device_description"])}</td><td>{e(start)}</td>'
                f'<td>{e(end)}</td><td><a href="{e(a["source_url"])}">source</a></td></tr>'
            )
        rows = ''.join(rows)
        table = f'<table><thead><tr><th>Producer</th><th>Brand/Family</th><th>Device</th><th>Start</th><th>End</th><th>Source</th></tr></thead><tbody>{rows}</tbody></table>'
    return render_page(title='Conditional Approvals', body=render('approvals.html', {'approval_table': Safe(table)}), root=root)


def build_myths(root: str = '') -> str:
    """Render the myth checks page."""
    claims = load_json('claims.json')
    if not claims:
        claims_html = '<p>No myths or claims available.</p>'
    else:
        claims_html = ''.join(
            f'<article class="card"><h2>{e(c["claim"])}</h2>'
            f'<p class="verdict-{css_class(c["verdict"])}">Verdict: {e(c["verdict"])}</p>'
            f'<p>{e(c["explanation"])}</p>'
            f'<p><strong>Guidance:</strong> {e(c.get("consumer_guidance", ""))}</p></article>'
            for c in claims
        )
    return render_page(title='Myth Checks', body=render('myths.html', {'claims': Safe(claims_html)}), root=root)


def build_sources(root: str = '') -> str:
    """Render the primary sources page."""
    sources = load_json('sources.json')
    if not sources:
        sources_html = '<p>No sources available.</p>'
    else:
        items = []
        for s in sources:
            pub_date = s.get("publication_date")
            date_part = f'{e(pub_date)}, ' if pub_date else ''
            items.append(
                f'<li><a href="{e(s["url"])}">{e(s["title"])}</a> '
                f'({date_part}{e(s["source_type"])})<br>'
                f'<span class="source-link">{e(s.get("summary", ""))}</span></li>'
            )
        sources_html = '<ul>' + ''.join(items) + '</ul>'
    return render_page(title='Sources', body=render('sources.html', {'sources': Safe(sources_html)}), root=root)


def build_search(root: str = '') -> str:
    """Render the search page."""
    body = render('search.html', {'root': root})
    return render_page(title='Search', body=body, root=root)


def main() -> int:
    global SITE_DATA_DIR, SITE_DIR

    parser = argparse.ArgumentParser(description='Render static HTML from site-data JSON.')
    parser.add_argument('--site-data', default=str(SITE_DATA_DIR), help='input JSON directory')
    parser.add_argument('--site', default=str(SITE_DIR), help='output HTML directory')
    args = parser.parse_args()

    original_site_data_dir = SITE_DATA_DIR
    original_site_dir = SITE_DIR
    SITE_DATA_DIR = Path(args.site_data)
    SITE_DIR = Path(args.site)

    try:
        SITE_DIR.mkdir(parents=True, exist_ok=True)

        pages = {
            'index.html': build_home,
            'faqs/index.html': build_faqs,
            'timeline/index.html': build_timeline,
            'waivers/index.html': build_waivers,
            'approvals/index.html': build_approvals,
            'myths/index.html': build_myths,
            'sources/index.html': build_sources,
            'search/index.html': build_search,
        }

        for rel_path, builder in pages.items():
            target = SITE_DIR / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            depth = rel_path.count('/')
            root = '../' * depth
            target.write_text(builder(root), encoding='utf-8')

        static_target = SITE_DIR / 'static'
        if static_target.exists():
            shutil.rmtree(static_target)
        shutil.copytree(STATIC_DIR, static_target)

        # Copy search_index.json into search/ directory for local fetch
        (SITE_DIR / 'search' / 'search_index.json').write_text(
            (SITE_DATA_DIR / 'search_index.json').read_text(encoding='utf-8'),
            encoding='utf-8',
        )

        print(f'Wrote {len(pages)} pages and static assets to {SITE_DIR}')
    finally:
        SITE_DATA_DIR = original_site_data_dir
        SITE_DIR = original_site_dir

    return 0


if __name__ == '__main__':
    raise SystemExit(main())

