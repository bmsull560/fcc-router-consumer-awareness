# FCC Router Consumer Awareness Database

A SQLite-backed data package and starter API for a consumer-awareness website about the FCC Covered List action involving consumer routers produced in foreign countries.

Generated: 2026-07-09  
Current as of: 2026-07-09  
Suggested GitHub repo: `bmsull560/fcc-router-consumer-awareness`

This repository is designed for public explainers, FAQs, source-backed timelines, myth checks, alerts, and regulatory status summaries. It is **not** legal advice and **not** a SKU-level compliance database.

## What is included

```text
data/fcc_router_consumer_awareness.db   SQLite database
data/fcc_router_consumer_awareness.sql  Full SQL dump
app/sqlite_api.py                       Tiny stdlib-only JSON API server
scripts/validate_db.py                  Integrity, row-count, and view checks
scripts/export_site_json.py             Export common website datasets to JSON
scripts/build_site.py                   Generate static HTML site
tests/                                  Unit tests for build, export, and site output
examples/queries.sql                    Starter SQL for pages/API endpoints
docs/database_README.md                 Schema notes, row counts, and caveats
docs/source-caveats.md                  Publishing and refresh checklist
.github/workflows/validate-db.yml       CI database validation workflow
PUSH_TO_GITHUB.md                       Manual GitHub publish steps
```

## Quick start

Validate the database:

```bash
python3 scripts/validate_db.py
```

Run the local JSON API:

```bash
python3 app/sqlite_api.py
```

Open these endpoints:

```text
http://localhost:8000/healthz
http://localhost:8000/api/status
http://localhost:8000/api/faqs
http://localhost:8000/api/timeline
http://localhost:8000/api/alerts
http://localhost:8000/api/search?q=firmware
```

Export static JSON for a frontend or static-site generator:

```bash
python3 scripts/export_site_json.py
```

The exporter writes to `site-data/`, which is intentionally ignored by Git.

## Build the static website

```bash
python3 scripts/build_site.py
```

This writes generated HTML to `site/` (ignored by Git).

## Run tests

Install dev dependencies and run the test suite with coverage:

```bash
python3 -m pip install -e '.[dev]'
python3 -m pytest tests/ -v
```

## Code quality

```bash
python3 -m ruff format --check scripts app tests
python3 -m ruff check scripts app tests
python3 -m mypy scripts app tests
```

## Website-ready views

The database includes prebuilt views for common consumer-awareness pages:

- `vw_current_consumer_status` — homepage status panel
- `vw_router_timeline` — regulatory timeline
- `vw_active_conditional_approvals` — active Conditional Approval records
- `vw_expiring_soon_conditional_approvals` — approvals ending within 180 days
- `vw_active_waivers` — active/proposed waiver records
- `vw_public_faqs` — FAQ content with source URLs
- `vw_primary_sources` — primary-source document list

## Site search

If your SQLite build supports FTS5, the database includes a `search_index` table.

```sql
SELECT table_name, row_id, title,
       snippet(search_index, 3, '<mark>', '</mark>', '...', 16) AS snippet
FROM search_index
WHERE search_index MATCH 'firmware OR updates';
```

## Scope and caveats

Keep these distinctions visible in any website copy:

- This dataset covers FCC router-related Covered List, waiver, and Conditional Approval information.
- It should not be presented as a blanket instruction that consumers must discard existing routers.
- It should not be used for model-specific sale/import/compliance claims without checking live FCC records.
- The dataset has a `current_as_of` date and should be refreshed before production launch.

## License

No license has been selected. Add the license you want before publishing if you plan to allow reuse.
