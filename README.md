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
migrations/0001_baseline.sql            Versioned schema baseline
app/api.py                              FastAPI application server (runtime)
app/sqlite_api.py                       Standalone stdlib-only JSON API server
scripts/migrate.py                      Versioned SQLite migration runner
scripts/backup_db.py                    Integrity-checked database backups
scripts/restore_db.py                   Restore a backup after verification
scripts/validate_db.py                  Integrity, row-count, and view checks
scripts/export_site_json.py             Export common website datasets to JSON
scripts/build_site.py                   Generate static HTML site
Dockerfile                              Container image for the FastAPI app
docker-compose.yml                      Local Docker Compose orchestration
tests/                                  Unit tests for build, export, site output, API, migrations, backups, and restore
examples/queries.sql                    Starter SQL for pages/API endpoints
docs/database_README.md                 Schema notes, row counts, and caveats
docs/source-caveats.md                  Publishing and refresh checklist
docs/runbooks/                          Deployment, incident response, rollback, and disaster-recovery runbooks
.github/workflows/ci.yml                CI lint, test, and validation workflow
.github/workflows/release.yml           Build and push versioned images to GHCR
.github/workflows/rollback.yml          Re-tag a previous image as latest
PUSH_TO_GITHUB.md                       Manual GitHub publish steps
```

## Quick start

Validate the database:

```bash
python3 scripts/validate_db.py
```

Run the local JSON API:

```bash
make api
```

Open these endpoints:

```text
http://localhost:8000/healthz
http://localhost:8000/ready
http://localhost:8000/metrics
http://localhost:8000/api/status
http://localhost:8000/api/faqs
http://localhost:8000/api/timeline
http://localhost:8000/api/alerts
http://localhost:8000/api/sources
http://localhost:8000/api/search?q=firmware
```

## Rate limits

The `/api/search` endpoint is rate-limited to 30 requests per minute per client IP.

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

```bash
make test
```

## Development setup

```bash
make install
```

This creates `.venv/` and installs the project plus linting, formatting, type-checking, and testing tools.

## Run with Docker

Build and start the API with Docker Compose:

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`. Migrations run automatically on startup.

## Development commands

| Command | Purpose |
|---|---|
| `make lint` | Run `ruff` linting |
| `make format` | Auto-format with `ruff format` |
| `make type-check` | Run `mypy` |
| `make test` | Run the pytest suite with coverage |
| `make e2e` | Run end-to-end tests against a real uvicorn server |
| `make audit` | Run `pip-audit` dependency security scan |
| `make validate` | Validate the SQLite database |
| `make build` | Build the static website |
| `make backup` | Create a timestamped, integrity-checked backup |
| `make restore BACKUP=...` | Restore the database from a backup |
| `make api` | Run the FastAPI development server |
| `make pre-commit` | Run pre-commit hooks on all files |

## CI

GitHub Actions runs lint, format check, type check, tests across Python 3.10–3.12, database validation, static-site build, and dependency auditing on every push and pull request.

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

## Architecture and operations

- [Architecture and Ownership](./docs/architecture.md)
- [Deployment Runbook](./docs/runbooks/deployment.md)
- [Release and Upgrade Runbook](./docs/runbooks/release-upgrade.md)
- [Incident Response Runbook](./docs/runbooks/incident-response.md)
- [Rollback Runbook](./docs/runbooks/rollback.md)
- [Disaster Recovery Runbook](./docs/runbooks/disaster-recovery.md)
- [SLOs and Alert Examples](./docs/runbooks/slos-alerts.md)
- [Load-Testing Runbook](./docs/runbooks/load-testing.md)

## Scope and caveats

Keep these distinctions visible in any website copy:

- This dataset covers FCC router-related Covered List, waiver, and Conditional Approval information.
- It should not be presented as a blanket instruction that consumers must discard existing routers.
- It should not be used for model-specific sale/import/compliance claims without checking live FCC records.
- The dataset has a `current_as_of` date and should be refreshed before production launch.

## License

This project is released into the public domain under the [CC0 1.0 Universal](LICENSE) license.
