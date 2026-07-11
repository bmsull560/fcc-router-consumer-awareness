#!/usr/bin/env python3
"""Render static HTML pages from site-data JSON using stdlib templates."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from collections.abc import Callable
from pathlib import Path
from string import Template
from typing import TypeVar

from scripts.models import (
    FAQ,
    Alert,
    Claim,
    ConditionalApproval,
    ConsumerStatus,
    PrimarySource,
    TimelineEvent,
    Waiver,
)

ROOT = Path(__file__).resolve().parents[1]
SITE_DATA_DIR = ROOT / 'site-data'
SITE_DIR = ROOT / 'site'
TEMPLATE_DIR = ROOT / 'site' / 'templates'
STATIC_DIR = ROOT / 'site' / 'static'

HOME_PREVIEW_LIMIT = 3

_T = TypeVar('_T')


def load_json(name: str) -> object:
    """Load raw JSON from the site-data directory."""
    path = SITE_DATA_DIR / name
    return json.loads(path.read_text(encoding='utf-8'))


def _load_list(name: str, model_ctor: Callable[[dict[str, object]], _T]) -> list[_T]:
    """Load a list-shaped JSON file and coerce each element through a model constructor."""
    raw = load_json(name)
    items: list[object]
    if isinstance(raw, dict):
        items = [raw]
    elif isinstance(raw, list):
        items = raw
    else:
        return []
    return [model_ctor(item) for item in items if isinstance(item, dict)]


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
                f'Template value for {k!r} must be str, Safe, or scalar; got {type(v).__name__}'
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
    statuses = _load_list('current_status.json', ConsumerStatus.from_dict)
    status = statuses[0] if statuses else ConsumerStatus.from_dict({})

    alerts = _load_list('alerts.json', Alert.from_dict)
    faqs = _load_list('faqs.json', FAQ.from_dict)
    timeline = _load_list('timeline.json', TimelineEvent.from_dict)

    alerts_html = (
        ''.join(_alert_card(a) for a in alerts)
        if alerts
        else '<p class="source-link">No active alerts.</p>'
    )

    faqs_html = (
        ''.join(
            f'<article class="faq-card"><div class="faq-icon">?</div>'
            f'<h3>{e(f.question)}</h3><p>{e(f.answer_short)}</p></article>'
            for f in faqs[:HOME_PREVIEW_LIMIT]
        )
        if faqs
        else '<p class="source-link">No FAQs available.</p>'
    )

    timeline_sorted = sorted(timeline, key=lambda ev: ev.event_date, reverse=True)
    timeline_html = (
        ''.join(_timeline_item(ev) for ev in timeline_sorted[:HOME_PREVIEW_LIMIT])
        if timeline
        else '<p class="source-link">No timeline events available.</p>'
    )

    body = render(
        'status.html',
        {
            'headline': status.headline,
            'continued_use_note': status.continued_use_note,
            'update_note': status.update_note,
            'verification_note': status.verification_note,
            'alerts': Safe(alerts_html),
            'faqs': Safe(faqs_html),
            'timeline': Safe(timeline_html),
            'root': root,
        },
    )
    return render_page(
        title='Home',
        body=body,
        current_as_of=status.current_as_of.isoformat(),
        root=root,
    )


def source_links(urls: str) -> str:
    """Turn a pipe-separated list of source URLs into HTML links."""
    if not urls:
        return ''
    parts = [u.strip() for u in str(urls).split('|') if u.strip()]
    return ' | '.join(f'<a href="{e(u)}">{e(u)}</a>' for u in parts)


_ALERT_ICONS = {
    'notice': 'ℹ',
    'info': '✓',
    'warning': '⚠',
    'urgent': '✕',
}


def _alert_card(a: Alert) -> str:
    """Render a single styled alert card."""
    severity = css_class(a.severity)
    icon = _ALERT_ICONS.get(severity, 'ℹ')
    cta_html = ''
    if a.cta_url:
        label = a.cta_label or 'Learn more'
        cta_html = f'<a href="{e(a.cta_url)}">{e(label)}</a>'
    return (
        f'<div class="alert-card alert-{severity}">'
        f'<div class="alert-bar"></div>'
        f'<div class="alert-inner">'
        f'<div class="alert-icon" aria-hidden="true">{icon}</div>'
        f'<div class="alert-content">'
        f'<h3>{e(a.title)}</h3>'
        f'<p>{e(a.body)}</p>'
        f'{cta_html}'
        f'</div></div></div>'
    )


def _timeline_item(ev: TimelineEvent, *, tag: str = 'div', include_source: bool = False) -> str:
    """Render a single styled timeline entry."""
    source_html = ''
    if include_source:
        source_html = (
            f'<p class="source-link"><strong>Consumer impact:</strong> {e(ev.consumer_impact)}</p>'
            f'<p class="source-link"><a href="{e(ev.source_url)}">Source: {e(ev.source_title)}</a></p>'
        )
    return (
        f'<{tag} class="timeline-item">'
        f'<div class="timeline-date">{e(ev.event_date)}</div>'
        f'<h3>{e(ev.title)}</h3>'
        f'<p>{e(ev.summary)}</p>'
        f'{source_html}'
        f'</{tag}>'
    )


def build_faqs(root: str = '') -> str:
    """Render the FAQ page from site-data JSON, grouped by category."""
    faqs = _load_list('faqs.json', FAQ.from_dict)
    if not faqs:
        body = render(
            'faqs.html',
            {'faq_groups': Safe('<p class="source-link">No FAQs available.</p>')},
        )
        return render_page(title='FAQs', body=body, root=root)

    by_category: dict[str, list[FAQ]] = {}
    for f in faqs:
        by_category.setdefault(f.category, []).append(f)

    groups = []
    for category, items in sorted(by_category.items()):
        items_html = ''.join(
            f'<article class="card"><h3>{e(item.question)}</h3>'
            f'<p><strong>Short answer:</strong> {e(item.answer_short)}</p>'
            f'<p>{e(item.answer_long)}</p>'
            f'{_faq_sources_html(item.source_urls)}</article>'
            for item in items
        )
        groups.append(f'<h2 class="category-title">{e(category)}</h2>{items_html}')

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
    events = _load_list('timeline.json', TimelineEvent.from_dict)
    if not events:
        events_html = '<p class="source-link">No timeline events available.</p>'
    else:
        events_sorted = sorted(events, key=lambda ev: ev.event_date, reverse=True)
        events_html = ''.join(
            _timeline_item(ev, tag='article', include_source=True) for ev in events_sorted
        )
    return render_page(
        title='Timeline',
        body=render('timeline.html', {'events': Safe(events_html)}),
        root=root,
    )


def build_waivers(root: str = '') -> str:
    """Render the active waivers page."""
    waivers = _load_list('waivers.json', Waiver.from_dict)
    if not waivers:
        table = '<p class="source-link">No waivers available.</p>'
    else:
        rows = ''.join(
            f'<tr><td>{e(w.waiver_type)}</td><td>{e(w.party)}</td>'
            f'<td>{e(w.equipment_scope)}</td><td>{e(w.effective_start_date)}</td>'
            f'<td>{e(w.effective_end_date)}</td>'
            f'<td><a href="{e(w.source_url)}">source</a></td></tr>'
            for w in waivers
        )
        table = f'<table><thead><tr><th>Type</th><th>Party</th><th>Scope</th><th>Start</th><th>End</th><th>Source</th></tr></thead><tbody>{rows}</tbody></table>'
    return render_page(
        title='Waivers', body=render('waivers.html', {'waiver_table': Safe(table)}), root=root
    )


def build_approvals(root: str = '') -> str:
    """Render the conditional approvals page."""
    approvals = _load_list('conditional_approvals.json', ConditionalApproval.from_dict)
    if not approvals:
        table = '<p class="source-link">No conditional approvals available.</p>'
    else:
        rows = ''.join(
            f'<tr><td>{e(a.producer)}</td><td>{e(a.brand_or_product_family)}</td>'
            f'<td>{e(a.device_description)}</td><td>{e(a.approval_start_date)}</td>'
            f'<td>{e(a.approval_end_date)}</td><td><a href="{e(a.source_url)}">source</a></td></tr>'
            for a in approvals
        )
        table = f'<table><thead><tr><th>Producer</th><th>Brand/Family</th><th>Device</th><th>Start</th><th>End</th><th>Source</th></tr></thead><tbody>{rows}</tbody></table>'
    return render_page(
        title='Conditional Approvals',
        body=render('approvals.html', {'approval_table': Safe(table)}),
        root=root,
    )


def build_myths(root: str = '') -> str:
    """Render the myth checks page."""
    claims = _load_list('claims.json', Claim.from_dict)
    if not claims:
        claims_html = '<p class="source-link">No myths or claims available.</p>'
    else:
        claims_html = ''.join(
            f'<article class="card"><h2>{e(c.claim)}</h2>'
            f'<p class="verdict-{css_class(c.verdict)}">Verdict: {e(c.verdict)}</p>'
            f'<p>{e(c.explanation)}</p>'
            f'<p><strong>Guidance:</strong> {e(c.consumer_guidance)}</p></article>'
            for c in claims
        )
    return render_page(
        title='Myth Checks', body=render('myths.html', {'claims': Safe(claims_html)}), root=root
    )


def build_sources(root: str = '') -> str:
    """Render the primary sources page."""
    sources = _load_list('sources.json', PrimarySource.from_dict)
    if not sources:
        sources_html = '<p class="source-link">No sources available.</p>'
    else:
        items = []
        for s in sources:
            date_part = f'{e(s.publication_date)}, ' if s.publication_date else ''
            items.append(
                f'<li><a href="{e(s.url)}">{e(s.title)}</a> '
                f'({date_part}{e(s.source_type)})<br>'
                f'<span class="source-link">{e(s.summary)}</span></li>'
            )
        sources_html = '<ul>' + ''.join(items) + '</ul>'
    return render_page(
        title='Sources', body=render('sources.html', {'sources': Safe(sources_html)}), root=root
    )


def build_search(root: str = '') -> str:
    """Render the search page."""
    body = render('search.html', {'root': root})
    return render_page(title='Search', body=body, root=root)


def main(argv: list[str] | None = None) -> int:
    global SITE_DATA_DIR, SITE_DIR

    parser = argparse.ArgumentParser(description='Render static HTML from site-data JSON.')
    parser.add_argument('--site-data', default=str(SITE_DATA_DIR), help='input JSON directory')
    parser.add_argument('--site', default=str(SITE_DIR), help='output HTML directory')
    args = parser.parse_args(argv)

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
        if static_target.resolve() != STATIC_DIR.resolve():
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
