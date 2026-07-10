#!/usr/bin/env python3
"""Render static HTML pages from site-data JSON using stdlib templates."""
from __future__ import annotations

import html
import json
import shutil
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parents[1]
SITE_DATA_DIR = ROOT / 'site-data'
SITE_DIR = ROOT / 'site'
TEMPLATE_DIR = ROOT / 'site' / 'templates'
STATIC_DIR = ROOT / 'site' / 'static'


def load_json(name: str) -> list[dict[str, object]] | dict[str, object]:
    path = SITE_DATA_DIR / name
    return json.loads(path.read_text(encoding='utf-8'))


def e(value: object) -> str:
    """HTML-escape a value."""
    return html.escape(str(value), quote=True)


class Safe:
    """Wrapper for pre-escaped HTML that should not be double-escaped."""
    def __init__(self, html: str):
        self.html = html

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
            safe[k] = v
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
