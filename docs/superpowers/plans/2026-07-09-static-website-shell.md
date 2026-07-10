# Static Website Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a vanilla HTML/CSS/JS static website shell from the existing SQLite database, with a stdlib-only Python build pipeline, client-side search, source citations, and tests.

**Architecture:** A two-stage build: `scripts/export_site_json.py` reads SQLite views and writes `site-data/*.json`; `scripts/build_html.py` reads only those JSON files and renders static pages via `string.Template`. `scripts/build_site.py` orchestrates export → render. Client-side search runs against a precomputed `search_index.json`.

**Tech Stack:** Python 3 standard library only (`sqlite3`, `json`, `string.Template`, `html`, `pathlib`, `unittest`), vanilla HTML/CSS/JS.

---

## Task 0: Bootstrap directories and gitignore

**Files:**
- Create: `site/templates/.gitkeep`
- Create: `site/static/.gitkeep`
- Create: `tests/__init__.py`
- Modify: `.gitignore`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p site/templates site/static tests
```

- [ ] **Step 2: Update `.gitignore`**

Append:

```text
# Generated site outputs
site-data/
site/*
!site/templates/
!site/templates/**
!site/static/
!site/static/**
```

Verify `site-data/` is already ignored; the `site/*` rule ignores generated HTML while the negation rules keep `site/templates/` and `site/static/` source files tracked.

- [ ] **Step 3: Commit**

```bash
git add .gitignore site/templates/.gitkeep site/static/.gitkeep tests/__init__.py
git commit -m "chore: bootstrap site dirs and tests"
```

---

## Task 1: Export `search_index.json`

**Files:**
- Modify: `scripts/export_site_json.py`
- Test: `tests/test_export.py`

- [ ] **Step 1: Write failing test**

In `tests/test_export.py`:

```python
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestExportJson(unittest.TestCase):
    def test_exports_search_index_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(ROOT / 'scripts' / 'export_site_json.py'), '--out', tmp],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            path = Path(tmp) / 'search_index.json'
            self.assertTrue(path.exists())
            data = json.loads(path.read_text(encoding='utf-8'))
            self.assertIsInstance(data, list)
            if data:
                self.assertIn('table_name', data[0])
                self.assertIn('row_id', data[0])
                self.assertIn('title', data[0])
                self.assertIn('snippet', data[0])
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m unittest tests.test_export.TestExportJson.test_exports_search_index_json -v
```

Expected: FAIL because `search_index.json` is not produced.

- [ ] **Step 3: Modify `scripts/export_site_json.py`**

Add to `EXPORTS`:

```python
'search_index.json': '''
    SELECT
        table_name,
        row_id,
        title,
        snippet(search_index, 3, '<mark>', '</mark>', '...', 16) AS snippet
    FROM search_index
    LIMIT 1000
''',
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m unittest tests.test_export.TestExportJson.test_exports_search_index_json -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/export_site_json.py tests/test_export.py
git commit -m "feat: export FTS5 search_index to JSON"
```

---

## Task 2: Shared template helper and base template

**Files:**
- Create: `site/templates/base.html`
- Create: `scripts/build_html.py`
- Test: `tests/test_build.py`

- [ ] **Step 1: Write failing test**

In `tests/test_build.py`:

```python
import tempfile
import unittest
from pathlib import Path

from scripts.build_html import render_page


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
```

- [ ] **Step 2: Run test**

```bash
python -m unittest tests.test_build.TestBuildHtml.test_render_page_includes_title_and_body -v
```

Expected: FAIL because `scripts/build_html.py` does not exist.

- [ ] **Step 3: Create `site/templates/base.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>$title | FCC Router Consumer Awareness</title>
  <link rel="stylesheet" href="${root}static/style.css">
</head>
<body>
  <header class="site-header">
    <nav class="container">
      <a class="logo" href="${root}">FCC Router Consumer Awareness</a>
      <ul class="nav-links">
        <li><a href="${root}faqs/">FAQs</a></li>
        <li><a href="${root}timeline/">Timeline</a></li>
        <li><a href="${root}approvals/">Approvals</a></li>
        <li><a href="${root}waivers/">Waivers</a></li>
        <li><a href="${root}myths/">Myths</a></li>
        <li><a href="${root}sources/">Sources</a></li>
        <li><a href="${root}search/">Search</a></li>
      </ul>
    </nav>
  </header>

  <main class="container">
    $body
  </main>

  <footer class="site-footer">
    <div class="container">
      <p><strong>Current as of $current_as_of.</strong></p>
      <p>This site is informational only and is not legal advice.</p>
      <p>It is not a SKU-level compliance database. Check live FCC records before making model-specific claims.</p>
    </div>
  </footer>
</body>
</html>
```

- [ ] **Step 4: Create `scripts/build_html.py` with `render_page`**

```python
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
```

- [ ] **Step 5: Run test**

```bash
python -m unittest tests.test_build.TestBuildHtml.test_render_page_includes_title_and_body -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add site/templates/base.html scripts/build_html.py tests/test_build.py
git commit -m "feat: add base template and render helper"
```

---

## Task 3: Shared CSS

**Files:**
- Create: `site/static/style.css`
- Test: `tests/test_site.py` (smoke test)

- [ ] **Step 1: Write failing test**

In `tests/test_site.py`:

```python
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestSiteAssets(unittest.TestCase):
    def test_style_css_exists(self):
        self.assertTrue((ROOT / 'site' / 'static' / 'style.css').exists())
```

- [ ] **Step 2: Run test**

```bash
python -m unittest tests.test_site.TestSiteAssets.test_style_css_exists -v
```

Expected: FAIL.

- [ ] **Step 3: Create `site/static/style.css`**

```css
:root {
  --color-bg: #ffffff;
  --color-text: #1a1a1a;
  --color-muted: #555555;
  --color-accent: #1f4e79;
  --color-accent-light: #e8f1f8;
  --color-border: #d1d5da;
  --color-warning: #fff3cd;
  --color-danger: #f8d7da;
  --font-stack: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --max-width: 800px;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  font-family: var(--font-stack);
  color: var(--color-text);
  background: var(--color-bg);
  line-height: 1.6;
}

.container {
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 0 1rem;
}

.site-header {
  background: var(--color-accent);
  color: #fff;
  padding: 1rem 0;
}

.site-header a { color: #fff; text-decoration: none; }

.site-header nav {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1rem;
}

.logo { font-weight: 700; font-size: 1.1rem; }

.nav-links {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

main { padding: 2rem 0; }

h1, h2, h3 { color: var(--color-accent); line-height: 1.2; }

a { color: var(--color-accent); }

.card {
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 1rem;
  margin-bottom: 1rem;
  background: var(--color-accent-light);
}

.alert {
  border-left: 4px solid var(--color-accent);
  padding: 1rem;
  margin-bottom: 1rem;
  background: var(--color-warning);
}

.alert-urgent { background: var(--color-danger); border-color: #721c24; }
.alert-warning { background: var(--color-warning); border-color: #856404; }

.source-link {
  font-size: 0.9rem;
  color: var(--color-muted);
}

footer {
  border-top: 1px solid var(--color-border);
  padding: 2rem 0;
  color: var(--color-muted);
  font-size: 0.9rem;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
}

th, td {
  text-align: left;
  padding: 0.5rem;
  border-bottom: 1px solid var(--color-border);
}

th { background: var(--color-accent-light); }

.verdict-true { color: #155724; font-weight: bold; }
.verdict-false { color: #721c24; font-weight: bold; }
.verdict-mixed { color: #856404; font-weight: bold; }

.search-input {
  width: 100%;
  padding: 0.75rem;
  font-size: 1rem;
  border: 1px solid var(--color-border);
  border-radius: 4px;
}

.search-result {
  margin-bottom: 1.5rem;
}
```

- [ ] **Step 4: Run test**

```bash
python -m unittest tests.test_site.TestSiteAssets.test_style_css_exists -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add site/static/style.css tests/test_site.py
git commit -m "feat: add shared site stylesheet"
```

---

## Task 4: Build home page

**Files:**
- Create: `site/templates/status.html`
- Modify: `scripts/build_html.py` (add `build_home`)
- Test: `tests/test_build.py`

- [ ] **Step 1: Write failing test**

```python
    def test_home_page_contains_status_and_alerts(self):
        from scripts.build_html import build_home
        html = build_home()
        self.assertIn('FCC Router Consumer Awareness', html)
        self.assertIn('Current as of', html)
```

- [ ] **Step 2: Run test**

Expected: FAIL.

- [ ] **Step 3: Create `site/templates/status.html`**

```html
<h1>What does the FCC router action mean for consumers?</h1>

<div class="card">
  <h2>$headline</h2>
  <p>$continued_use_note</p>
  <p>$update_note</p>
  <p class="source-link">$verification_note</p>
</div>

<h2>Active alerts</h2>
$alerts

<h2>Top questions</h2>
$faqs

<h2>Latest timeline events</h2>
$timeline
```

- [ ] **Step 4: Add `build_home` to `scripts/build_html.py`**

```python
def build_home(root: str = '') -> str:
    status = load_json('current_status.json')[0]
    alerts = load_json('alerts.json')
    faqs = load_json('faqs.json')
    timeline = load_json('timeline.json')

    alerts_html = ''.join(
        f'<div class="alert alert-{a["severity"]}"><strong>{e(a["title"])}</strong><p>{e(a["body"])}</p></div>'
        for a in alerts
    ) if alerts else '<p>No active alerts.</p>'

    faqs_html = ''.join(
        f'<article class="card"><h3>{e(f["question"])}</h3><p>{e(f["answer_short"])}</p></article>'
        for f in faqs[:3]
    )

    timeline_html = '<ul>' + ''.join(
        f'<li><strong>{e(e["event_date"])}</strong> — {e(e["title"])}<br>{e(e["summary"])}</li>'
        for e in timeline[:3]
    ) + '</ul>'

    body = render(
        'status.html',
        {
            'headline': status['headline'],
            'continued_use_note': status['continued_use_note'],
            'update_note': status['update_note'],
            'verification_note': status['verification_note'],
            'alerts': Safe(alerts_html),
            'faqs': Safe(faqs_html),
            'timeline': Safe(timeline_html),
        },
    )
    return render_page(title='Home', body=body, root=root)
```

- [ ] **Step 5: Run test**

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add site/templates/status.html scripts/build_html.py tests/test_build.py
git commit -m "feat: build home page"
```

---

## Task 5: Build FAQ page

**Files:**
- Create: `site/templates/faqs.html`
- Modify: `scripts/build_html.py`
- Test: `tests/test_build.py`

- [ ] **Step 1: Write failing test**

```python
    def test_faq_page_contains_questions(self):
        from scripts.build_html import build_faqs
        html = build_faqs()
        self.assertIn('FAQs', html)
```

- [ ] **Step 2: Run test**

Expected: FAIL.

- [ ] **Step 3: Create `site/templates/faqs.html`**

```html
<h1>Frequently Asked Questions</h1>
$faq_groups
```

- [ ] **Step 4: Add `build_faqs` to `scripts/build_html.py`**

```python
def build_faqs(root: str = '') -> str:
    faqs = load_json('faqs.json')
    by_category: dict[str, list[dict[str, object]]] = {}
    for f in faqs:
        by_category.setdefault(f['category'], []).append(f)

    groups = []
    for category, items in sorted(by_category.items()):
        items_html = ''.join(
            f'<article class="card"><h3>{e(item["question"])}</h3>'
            f'<p><strong>Short answer:</strong> {e(item["answer_short"])}</p>'
            f'<p>{e(item["answer_long"])}</p>'
            f'<p class="source-link">Sources: {source_links(item.get("source_urls", ""))}</p></article>'
            for item in items
        )
        groups.append(f'<h2>{e(category)}</h2>{items_html}')

    body = render('faqs.html', {'faq_groups': Safe(''.join(groups))})
    return render_page(title='FAQs', body=body, root=root)


def source_links(urls: str) -> str:
    if not urls:
        return ''
    parts = [u.strip() for u in str(urls).split('|') if u.strip()]
    return ' | '.join(f'<a href="{e(u)}">{e(u)}</a>' for u in parts)
```

- [ ] **Step 5: Run test**

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add site/templates/faqs.html scripts/build_html.py tests/test_build.py
git commit -m "feat: build FAQ page"
```

---

## Task 6: Build timeline, waivers, approvals, myths, sources pages

**Files:**
- Create: `site/templates/timeline.html`, `waivers.html`, `approvals.html`, `myths.html`, `sources.html`
- Modify: `scripts/build_html.py`
- Test: `tests/test_build.py`

- [ ] **Step 1: Write failing tests**

```python
    def test_timeline_page_contains_events(self):
        from scripts.build_html import build_timeline
        html = build_timeline()
        self.assertIn('Timeline', html)

    def test_waivers_page_contains_waivers(self):
        from scripts.build_html import build_waivers
        html = build_waivers()
        self.assertIn('Waivers', html)

    def test_approvals_page_contains_approvals(self):
        from scripts.build_html import build_approvals
        html = build_approvals()
        self.assertIn('Conditional Approvals', html)

    def test_myths_page_contains_claims(self):
        from scripts.build_html import build_myths
        html = build_myths()
        self.assertIn('Myths', html)

    def test_sources_page_contains_sources(self):
        from scripts.build_html import build_sources
        html = build_sources()
        self.assertIn('Sources', html)
```

- [ ] **Step 2: Run tests**

Expected: FAIL (functions missing).

- [ ] **Step 3: Create templates**

`site/templates/timeline.html`:

```html
<h1>Regulatory Timeline</h1>
$events
```

`site/templates/waivers.html`:

```html
<h1>Active Waivers</h1>
$waiver_table
```

`site/templates/approvals.html`:

```html
<h1>Conditional Approvals</h1>
$approval_table
```

`site/templates/myths.html`:

```html
<h1>Myth Checks</h1>
$claims
```

`site/templates/sources.html`:

```html
<h1>Primary Sources</h1>
$sources
```

- [ ] **Step 4: Add builders to `scripts/build_html.py`**

```python
def build_timeline(root: str = '') -> str:
    events = load_json('timeline.json')
    events_html = ''.join(
        f'<article class="card"><h2>{e(e["event_date"])} — {e(e["title"])}</h2>'
        f'<p><span class="label">Type:</span> {e(e["event_type"])}</p>'
        f'<p>{e(e["summary"])}</p>'
        f'<p><strong>Consumer impact:</strong> {e(e.get("consumer_impact", ""))}</p>'
        f'<p class="source-link"><a href="{e(e["source_url"])}">Source: {e(e["source_title"])}</a></p></article>'
        for e in events
    )
    return render_page(title='Timeline', body=render('timeline.html', {'events': Safe(events_html)}), root=root)


def build_waivers(root: str = '') -> str:
    waivers = load_json('waivers.json')
    rows = ''.join(
        f'<tr><td>{e(w["waiver_type"])}</td><td>{e(w["party"])}</td>'
        f'<td>{e(w["equipment_scope"])}</td><td>{e(w.get("effective_start_date", ""))}</td>'
        f'<td>{e(w.get("effective_end_date", "open-ended"))}</td>'
        f'<td><a href="{e(w["source_url"])}">source</a></td></tr>'
        for w in waivers
    )
    table = f'<table><thead><tr><th>Type</th><th>Party</th><th>Scope</th><th>Start</th><th>End</th><th>Source</th></tr></thead><tbody>{rows}</tbody></table>'
    return render_page(title='Waivers', body=render('waivers.html', {'waiver_table': Safe(table)}), root=root)


def build_approvals(root: str = '') -> str:
    approvals = load_json('conditional_approvals.json')
    rows = ''.join(
        f'<tr><td>{e(a["producer"])}</td><td>{e(a.get("brand_or_product_family", ""))}</td>'
        f'<td>{e(a["device_description"])}</td><td>{e(a["approval_start_date"])}</td>'
        f'<td>{e(a["approval_end_date"])}</td><td><a href="{e(a["source_url"])}">source</a></td></tr>'
        for a in approvals
    )
    table = f'<table><thead><tr><th>Producer</th><th>Brand/Family</th><th>Device</th><th>Start</th><th>End</th><th>Source</th></tr></thead><tbody>{rows}</tbody></table>'
    return render_page(title='Conditional Approvals', body=render('approvals.html', {'approval_table': Safe(table)}), root=root)


def build_myths(root: str = '') -> str:
    claims = load_json('claims.json')
    claims_html = ''.join(
        f'<article class="card"><h2>{e(c["claim"])}</h2>'
        f'<p class="verdict-{e(c["verdict"])}">Verdict: {e(c["verdict"])}</p>'
        f'<p>{e(c["explanation"])}</p>'
        f'<p><strong>Guidance:</strong> {e(c.get("consumer_guidance", ""))}</p></article>'
        for c in claims
    )
    return render_page(title='Myth Checks', body=render('myths.html', {'claims': Safe(claims_html)}), root=root)


def build_sources(root: str = '') -> str:
    sources = load_json('sources.json')
    sources_html = '<ul>' + ''.join(
        f'<li><a href="{e(s["url"])}">{e(s["title"])}</a> '
        f'({e(s.get("publication_date", ""))}, {e(s["source_type"])})<br>'
        f'<span class="source-link">{e(s.get("summary", ""))}</span></li>'
        for s in sources
    ) + '</ul>'
    return render_page(title='Sources', body=render('sources.html', {'sources': Safe(sources_html)}), root=root)
```

- [ ] **Step 5: Run tests**

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add site/templates/timeline.html site/templates/waivers.html site/templates/approvals.html site/templates/myths.html site/templates/sources.html scripts/build_html.py tests/test_build.py
git commit -m "feat: build timeline, waivers, approvals, myths, sources pages"
```

---

## Task 7: Build search page and client-side search

**Files:**
- Create: `site/templates/search.html`
- Create: `site/static/search.js`
- Modify: `scripts/build_html.py`
- Test: `tests/test_build.py`

- [ ] **Step 1: Write failing test**

```python
    def test_search_page_loads_index(self):
        from scripts.build_html import build_search
        html = build_search()
        self.assertIn('Search', html)
        self.assertIn('search_index.json', html)
```

- [ ] **Step 2: Run test**

Expected: FAIL.

- [ ] **Step 3: Create `site/templates/search.html`**

```html
<h1>Search</h1>
<input type="search" id="search-input" class="search-input" placeholder="Search for firmware, waivers, approvals...">
<div id="search-results"></div>
<script src="${root}static/search.js"></script>
```

- [ ] **Step 4: Add `build_search` to `scripts/build_html.py`**

```python
def build_search(root: str = '') -> str:
    body = render('search.html', {})
    return render_page(title='Search', body=body, root=root)
```

- [ ] **Step 5: Create `site/static/search.js`**

```javascript
(async function () {
  const input = document.getElementById('search-input');
  const resultsEl = document.getElementById('search-results');
  if (!input || !resultsEl) return;

  let index = [];
  try {
    const res = await fetch('search_index.json');
    if (res.ok) index = await res.json();
  } catch (err) {
    resultsEl.innerHTML = '<p>Could not load search index.</p>';
    return;
  }

  input.addEventListener('input', () => {
    const query = input.value.trim().toLowerCase();
    if (!query) {
      resultsEl.innerHTML = '';
      return;
    }
    const terms = query.split(/\s+/);
    const hits = index.filter(item => {
      const text = ((item.title || '') + ' ' + (item.snippet || '')).toLowerCase();
      return terms.every(term => text.includes(term));
    }).slice(0, 20);

    if (!hits.length) {
      resultsEl.innerHTML = '<p>No results found.</p>';
      return;
    }

    const html = hits.map(hit => `
      <div class="search-result">
        <h3>${escapeHtml(hit.title || 'Untitled')}</h3>
        <p class="source-link">${escapeHtml(hit.table_name || '')} #${escapeHtml(String(hit.row_id || ''))}</p>
        <p>${escapeHtml(hit.snippet || '')}</p>
      </div>
    `).join('');
    resultsEl.innerHTML = html;
  });

  function escapeHtml(str) {
    return str.replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }
})();
```

- [ ] **Step 6: Run test**

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add site/templates/search.html site/static/search.js scripts/build_html.py tests/test_build.py
git commit -m "feat: build search page with client-side search"
```

---

## Task 8: Orchestrator `build_site.py`

**Files:**
- Create: `scripts/build_site.py`
- Test: `tests/test_site.py`

- [ ] **Step 1: Write failing test**

```python
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestBuildSite(unittest.TestCase):
    def test_build_site_creates_all_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(ROOT / 'scripts' / 'build_site.py'), '--out', tmp],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            out = Path(tmp)
            self.assertTrue((out / 'index.html').exists())
            self.assertTrue((out / 'faqs' / 'index.html').exists())
            self.assertTrue((out / 'timeline' / 'index.html').exists())
            self.assertTrue((out / 'waivers' / 'index.html').exists())
            self.assertTrue((out / 'approvals' / 'index.html').exists())
            self.assertTrue((out / 'myths' / 'index.html').exists())
            self.assertTrue((out / 'sources' / 'index.html').exists())
            self.assertTrue((out / 'search' / 'index.html').exists())
```

- [ ] **Step 2: Run test**

Expected: FAIL.

- [ ] **Step 3: Create `scripts/build_site.py`**

```python
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
```

- [ ] **Step 4: Update `scripts/build_html.py` to accept CLI args**

Add at the bottom:

```python
def main() -> int:
    parser = argparse.ArgumentParser(description='Render static HTML from site-data JSON.')
    parser.add_argument('--site-data', default=str(SITE_DATA_DIR), help='input JSON directory')
    parser.add_argument('--site', default=str(SITE_DIR), help='output HTML directory')
    args = parser.parse_args()

    global SITE_DATA_DIR, SITE_DIR, TEMPLATE_DIR, STATIC_DIR
    SITE_DATA_DIR = Path(args.site_data)
    SITE_DIR = Path(args.site)
    TEMPLATE_DIR = ROOT / 'site' / 'templates'
    STATIC_DIR = ROOT / 'site' / 'static'

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
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
```

Also add `import argparse` at the top.

- [ ] **Step 5: Run test**

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/build_site.py scripts/build_html.py tests/test_site.py
git commit -m "feat: add build_site orchestrator and CLI args"
```

---

## Task 9: HTML escaping and internal link tests

**Files:**
- Test: `tests/test_build.py`

- [ ] **Step 1: Write tests**

```python
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
            import re
            hrefs = re.findall(r'href="([^"]+)"', html)
            for href in hrefs:
                if href.startswith('http') or href.startswith('#') or href.startswith('mailto:'):
                    continue
                parts = href.rstrip('/').split('/')
                candidate = site / Path(*parts)
                if href.endswith('/'):
                    candidate = candidate / 'index.html'
                self.assertTrue(candidate.exists(), f'Missing link target: {href}')
```

- [ ] **Step 2: Run tests**

```bash
python -m unittest tests.test_build -v
```

Expected: PASS after running `build_site.py` once or adjusting imports to build in memory.

- [ ] **Step 3: Commit**

```bash
git add tests/test_build.py
git commit -m "test: html escaping and internal link checks"
```

---

## Task 10: Determinism and repeatable build tests

**Files:**
- Test: `tests/test_export.py`, `tests/test_build.py`

- [ ] **Step 1: Write tests**

In `tests/test_export.py`:

```python
    def test_export_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
            subprocess.run([sys.executable, str(ROOT / 'scripts' / 'export_site_json.py'), '--out', tmp1], check=True)
            subprocess.run([sys.executable, str(ROOT / 'scripts' / 'export_site_json.py'), '--out', tmp2], check=True)
            for name in ['current_status.json', 'faqs.json', 'timeline.json', 'search_index.json']:
                a = Path(tmp1) / name
                b = Path(tmp2) / name
                self.assertEqual(a.read_bytes(), b.read_bytes(), f'{name} differs')
```

In `tests/test_build.py`:

```python
    def test_build_is_repeatable(self):
        import tempfile
        from scripts.build_html import main as build_main
        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp) / 'site'
            build_main(['--site-data', str(ROOT / 'site-data'), '--site', str(site)])
            first = (site / 'index.html').read_bytes()
            build_main(['--site-data', str(ROOT / 'site-data'), '--site', str(site)])
            second = (site / 'index.html').read_bytes()
            self.assertEqual(first, second)
```

- [ ] **Step 2: Run tests**

```bash
python -m unittest tests.test_export.TestExportJson.test_export_is_deterministic tests.test_build.TestBuildHtml.test_build_is_repeatable -v
```

Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test_export.py tests/test_build.py
git commit -m "test: deterministic export and repeatable builds"
```

---

## Task 11: Update CI workflow

**Files:**
- Modify: `.github/workflows/validate-db.yml`

- [ ] **Step 1: Update workflow**

Add steps after the export smoke test:

```yaml
      - name: Build static site
        run: python scripts/build_site.py
      - name: Run site tests
        run: python -m unittest discover tests -v
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/validate-db.yml
git commit -m "ci: build site and run tests in GitHub Actions"
```

---

## Task 12: Update README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add build/test section**

After the export section, add:

```markdown
## Build the static website

```bash
python scripts/build_site.py
```

This writes generated HTML to `site/` (ignored by Git).

## Run tests

```bash
python -m unittest discover tests -v
```
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add static site build and test instructions"
```

---

## Final verification

Run the full pipeline locally:

```bash
python scripts/validate_db.py
python scripts/build_site.py
python -m unittest discover tests -v
```

Expected: all commands exit 0 and tests pass.
