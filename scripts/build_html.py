#!/usr/bin/env python3
"""Render static HTML pages from site-data JSON using stdlib templates."""
from __future__ import annotations

import html
import json
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
    statuses = load_json('current_status.json')
    status = statuses[0] if statuses else {}
    alerts = load_json('alerts.json')
    faqs = load_json('faqs.json')
    timeline = load_json('timeline.json')

    alerts_html = ''.join(
        f'<div class="alert alert-{e(a["severity"])}"><strong>{e(a["title"])}</strong><p>{e(a["body"])}</p></div>'
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

