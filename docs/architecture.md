# Architecture and Ownership

## Overview

This repository is a SQLite-backed data package and a small FastAPI service that powers a consumer-awareness website about FCC Covered List actions involving consumer routers.

It is intentionally simple: a single-process Python API serves read-only data from a local SQLite file, with scheduled/operator-driven refresh jobs producing a new database and static site artifacts.

## Components

| Component | File(s) | Responsibility | Owner |
|-----------|---------|----------------|-------|
| FastAPI application | `app/api.py`, `app/models.py`, `app/config.py`, `app/db.py`, `app/logging.py`, `app/tracing.py` | HTTP API, request logging, metrics, rate limiting, health/readiness. | @bmsull560 |
| Standalone JSON API | `app/sqlite_api.py` | Stdlib-only alternative for constrained environments. | @bmsull560 |
| SQLite database | `data/fcc_router_consumer_awareness.db`, `data/fcc_router_consumer_awareness.sql` | Source data, views, FTS5 search index. | @bmsull560 |
| Migration runner | `scripts/migrate.py`, `migrations/` | Versioned schema migrations and baseline tracking. | @bmsull560 |
| Backup/restore | `scripts/backup_db.py`, `scripts/restore_db.py` | Integrity-checked backups and tested recovery. | @bmsull560 |
| Validation | `scripts/validate_db.py` | Integrity, row-count, and view checks. | @bmsull560 |
| Site generation | `scripts/build_site.py`, `scripts/build_html.py`, `scripts/export_site_json.py` | Export JSON datasets and generate static HTML. | @bmsull560 |
| Operational runbooks | `docs/runbooks/` | Deployment, incident response, rollback, disaster recovery, SLOs, load testing, release/upgrade. | @bmsull560 |
| CI/CD | `.github/workflows/` | Lint, test, type check, validate, build, dependency audit, release, rollback, E2E tests. | @bmsull560 |

## Data flow

1. Source data is maintained as a SQLite database (`data/fcc_router_consumer_awareness.db`) and a matching SQL dump (`data/fcc_router_consumer_awareness.sql`).
2. `scripts/validate_db.py` checks integrity and view counts before any build or deployment.
3. `scripts/export_site_json.py` and `scripts/build_site.py` produce `site-data/` and `site/` artifacts.
4. `scripts/migrate.py` applies schema migrations on startup or during deployment.
5. `scripts/backup_db.py` creates timestamped, integrity-checked `.gz` backups in `backups/`.
6. The FastAPI application (`app/api.py`) reads from the SQLite file and exposes JSON endpoints plus Prometheus metrics.

## Security and operational defaults

- No credentials are committed to source control.
- The Docker image runs as a non-root user (`appuser`).
- Rate limiting is enabled on `/api/search`.
- Security headers are added to all responses.
- Dependency vulnerabilities are scanned in CI and locally via `make audit`.
- All database restores pass `PRAGMA integrity_check` before replacing the live file.

## Decisions

- **SQLite for simplicity:** The dataset is small, read-mostly, and single-tenant. SQLite avoids operational database overhead while still supporting FTS5 search and migrations.
- **Static site + API:** The static site can be deployed to any static host; the API provides dynamic search and alerts.
- **Containerization:** Docker Compose provides a reproducible local production-like environment; GHCR hosts versioned images.
- **No authentication:** The API is intentionally public read-only. If write endpoints are added later, authentication and authorization must be introduced.
