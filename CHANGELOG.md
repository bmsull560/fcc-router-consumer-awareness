# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- (empty until next release)

## [0.1.0] - 2026-07-10

### Added
- Phase 1 production-readiness foundations: governance docs (`CONTRIBUTING.md`, `CODEOWNERS`, `SECURITY.md`, `CHANGELOG.md`), `Makefile`-based workflow, and project metadata in `pyproject.toml`.
- Initial SQLite-backed data package for FCC router consumer awareness.
- `app/sqlite_api.py` stdlib-only JSON API with health, status, timeline, FAQs, alerts, sources, and search endpoints.
- `app/api.py` FastAPI application with `/healthz`, `/ready`, `/api/status`, `/api/faqs`, `/api/timeline`, `/api/alerts`, `/api/sources`, and `/api/search` endpoints, plus Pydantic settings/models and integration tests.
- `scripts/validate_db.py`, `scripts/export_site_json.py`, `scripts/build_site.py`, and `scripts/build_html.py` for validation, export, and static-site generation.
- `scripts/migrate.py`, `migrations/0001_baseline.sql`, and migration tests for versioned schema management.
- `scripts/backup_db.py` and `scripts/restore_db.py` with integrity checks and round-trip tests.
- `Dockerfile`, `.dockerignore`, and `docker-compose.yml` for containerized deployment.
- `.github/workflows/release.yml` and `.github/workflows/rollback.yml` for CI/CD image publishing and rollback.
- Operational runbooks under `docs/runbooks/` covering deployment, incident response, rollback, disaster recovery, SLOs/alerts, load testing, release, and upgrade.
- `app/tracing.py` lightweight request tracing hook and `locustfile.py` load-test baseline.
- `tests/test_e2e.py` end-to-end tests against a real uvicorn server and `tests/test_integration_workflow.py` backup/restore/validate integration test.
- `make audit` and `make e2e` targets; dependency-audit and E2E jobs in CI.
- `docs/architecture.md` documenting system architecture, component ownership, data flow, and decisions.
- `tests/` covering HTML rendering, JSON export determinism, full site builds, API behavior, migrations, backups, restore, E2E, and integration workflows.
- `docs/database_README.md`, `docs/source-caveats.md`, and planning docs under `docs/superpowers/`.
- `LICENSE` (CC0-1.0).
