# Production-Readiness Design: FCC Router Consumer Awareness

## Context

The repository is a small Python data-package and starter website:

- `data/fcc_router_consumer_awareness.db` / `.sql` — SQLite dataset with sources, timeline, FAQs, claims, conditional approvals, waivers, alerts, and FTS5 search.
- `app/sqlite_api.py` — stdlib-only JSON API (`http.server`) exposing `/healthz`, `/api/status`, `/api/faqs`, `/api/timeline`, `/api/alerts`, `/api/sources`, `/api/search`.
- `scripts/` — `validate_db.py`, `export_site_json.py`, `build_site.py`, `build_html.py`.
- `site/` — static HTML templates and assets; `build_site.py` writes generated pages here.
- `tests/` — `unittest` tests for HTML rendering, JSON export determinism, and full site build.
- `.github/workflows/validate-db.yml` — CI that validates the DB, builds the site, and runs tests on every push/PR.

The current stack is functional for local development but lacks most production concerns: no dependency manifest, no linting/type-checking, a single-threaded stdlib HTTP server, no structured logging/metrics, no containerization, no versioned migrations, no release/rollback workflow, and no operational runbooks.

## Goal

Make the repository production-ready per the project’s Definition of Done, while keeping the existing data model and static-site output intact. The result must let a new engineer clone, run, test, and deploy the application with documented commands, and give an operator the artifacts needed to detect, diagnose, and recover from failures.

## Scope

This design covers the repository-level foundations and the JSON API service. The static site generator is preserved; deployment can be either the API service, the generated static site, or both. Out of scope for this design: sourcing new FCC data, changing the SQLite schema, and external monitoring-provider setup (runbooks will describe how to wire them).

## Approaches

### Option A — Harden the existing stdlib stack

Add `pyproject.toml`, linting/formatting/type-checking, pytest, expanded CI, documentation, and runbooks. Keep `http.server` as the API but document that it must run behind a reverse proxy and is intended for low-traffic or local use. Add a simple WSGI wrapper so it can be served by `gunicorn`.

- **Pros:** Minimal code churn, preserves stdlib-only character, fast to implement.
- **Cons:** `http.server` is not a production server; validation, metrics, graceful shutdown, and rate limiting require hand-rolled code.

### Option B — Modernize the API to FastAPI and containerize (recommended)

Replace the stdlib server with a FastAPI application, add Pydantic models and settings, structured logging, Prometheus metrics, rate limiting, health/readiness probes, and a Dockerfile using `gunicorn` + `uvicorn` workers. Keep the static-site builder as a separate, tested script. Add Alembic-style or versioned SQL migrations, backup/restore scripts, release/rollback GitHub Actions, and runbooks.

- **Pros:** Satisfies the largest number of Definition-of-Done items directly; strong input validation, observability, and operational ergonomics; standard Python deployment pattern.
- **Cons:** Adds dependencies; larger initial change than Option A.

### Option C — Static-site-first with optional dev API

Treat the generated static site as the production artifact and serve it with nginx/Caddy. Keep the API only as a local development helper. Add a scheduled refresh job that rebuilds the site and a simple deployment pipeline for the static files.

- **Pros:** Very low runtime complexity, cheap to host, high cacheability.
- **Cons:** Loses dynamic search/query behavior in production unless reimplemented client-side; does not exercise many production-readiness practices (authz, rate limiting, structured logging for an API).

**Recommendation:** Adopt **Option B** because the Definition of Done explicitly calls for input validation, authentication/authorization hooks, metrics, health checks, rate limiting, graceful error handling, and versioned migrations — all of which are straightforward with FastAPI and hard to do safely with the stdlib server. The static-site path remains available for users who prefer Option C later.

## Design

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         GitHub Actions                           │
│  lint / type-check / test / validate-db / build-site / image     │
└──────────────────────────────────┬──────────────────────────────┘
                                   │ push release tag
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  Container image (non-root user)                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  gunicorn    │──│   uvicorn    │──│   FastAPI app        │   │
│  │  workers     │  │   worker     │  │   /healthz /metrics  │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
│                           │                                      │
│                           ▼                                      │
│              data/fcc_router_consumer_awareness.db               │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
        scripts/build_site.py ──► site/ (static HTML + JSON)
```

### Components

| Component | Responsibility | Location |
|---|---|---|
| `app/api.py` | FastAPI app with all endpoints, exception handlers, and lifespan | `app/api.py` |
| `app/config.py` | Pydantic Settings for env-driven configuration | `app/config.py` |
| `app/db.py` | SQLite connection helper with query timeout and row factory | `app/db.py` |
| `app/models.py` | Pydantic request/response models | `app/models.py` |
| `app/logging.py` | Structured JSON logging setup | `app/logging.py` |
| `app/metrics.py` | Prometheus metrics instrument (via `prometheus-fastapi-instrumentator`) | `app/metrics.py` |
| `app/rate_limit.py` | In-memory rate limiting for search endpoint | `app/rate_limit.py` |
| `scripts/validate_db.py` | DB integrity, row/view counts, FTS5 sanity | unchanged behavior, refactored for testability |
| `scripts/export_site_json.py` | Deterministic JSON export from DB | unchanged interface |
| `scripts/build_site.py` / `build_html.py` | Static HTML generation | unchanged interface, covered by tests |
| `migrations/` | Versioned SQL migration files and a `migrate.py` runner | `migrations/versions/` |
| `tests/` | pytest unit + integration tests | `tests/` |
| `docs/runbooks/` | Operational runbooks | `docs/runbooks/` |

### Data flow

1. **Local dev / CI:** `scripts/validate_db.py` checks DB integrity and counts; `pytest` runs unit and API integration tests; `scripts/build_site.py` exports JSON and renders HTML.
2. **Runtime API:** FastAPI lifespan opens a read-only connection pool backed by the SQLite file. Each request executes a parameterized query, returns a Pydantic model, and emits a structured access log.
3. **Static publish:** `scripts/build_site.py` is run in CI or on a schedule; the resulting `site/` directory is deployed as a static artifact or served from the container.
4. **Release:** A GitHub release workflow builds the Docker image, tags it with the SemVer release tag, and pushes to GHCR. Rollback is redeploying the previous image tag.

### Error handling

- **Validation errors:** Handled by FastAPI/Pydantic and returned as `422` with a clear body.
- **Unhandled exceptions:** Global exception handler returns `500 {"error": "Internal server error", "trace_id": "..."}` and logs the full traceback with the trace ID.
- **Database errors:** Caught, logged, and returned as `503 Service Unavailable` when the DB is unreachable, `500` otherwise.
- **Timeouts:** SQLite `busy_timeout` and per-query `timeout` parameters prevent indefinite waits.
- **Rate limits:** Search endpoint returns `429` when the per-IP limit is exceeded.
- **Graceful shutdown:** Uvicorn handles SIGTERM; in-flight requests complete before the process exits.

### Security

- No credentials in source control; configuration is env-driven with sensible defaults.
- Input validation via Pydantic; SQL queries use parameter binding.
- CORS allowed origins are configurable and default to none.
- Response headers include `X-Content-Type-Options: nosniff` and `X-Frame-Options: DENY`.
- Dependency scanning via `pip-audit` in CI.
- Container runs as a non-root user and reads the database file read-only.
- **Authentication/authorization:** The public read-only endpoints require no auth. FastAPI dependency injection is used so that future admin/write endpoints can enforce API-key auth by adding a single dependency, without changing endpoint handlers.

### Testing

| Test type | What it covers |
|---|---|
| Unit | DB validation, deterministic JSON export, HTML escaping, CSS class sanitization, empty-state rendering |
| Integration | FastAPI `TestClient` exercises every endpoint including search, 404, 422, and 500 paths |
| Build | Full `build_site.py` run produces all expected pages and internal links resolve |
| E2E (optional) | Container health check and static file serving via `docker compose up` |

### Observability

- Structured JSON logs to stdout with level, timestamp, trace_id, path, method, status, and duration.
- `/healthz` returns `200 {"status": "ok"}`; a future `/ready` can verify DB accessibility.
- `/metrics` exposes Prometheus counters/histograms for requests and DB query durations.
- CI artifacts and container image labels include version and git SHA.

### Database migrations

Because the schema is small and the source of truth is the SQL dump, migrations are stored as ordered SQL files (`migrations/versions/001_initial.sql`, etc.) and applied by `migrations/migrate.py`. The migration table `schema_version` records the current version. Backup/restore runbooks use SQLite `.backup` and `.restore` commands.

### Versioning and release

- `pyproject.toml` uses SemVer; `CHANGELOG.md` follows Keep a Changelog.
- GitHub release workflow triggers on tags matching `v*.*.*`, runs the full CI matrix, builds and pushes the Docker image, and creates a release with notes.
- Rollback runbook: identify last known-good image tag and redeploy.

### Operational runbooks

- `docs/runbooks/deployment.md` — local Docker, CI release, and static-site publish steps.
- `docs/runbooks/incident-response.md` — symptom-to-check mapping, log/metric queries, escalation.
- `docs/runbooks/rollback.md` — container image rollback and static-site revert.
- `docs/runbooks/disaster-recovery.md` — DB backup/restore and full rebuild from `data/*.sql`.

## Phases

1. **Foundations** — `pyproject.toml`, dev tools (ruff, mypy, pytest, pre-commit), expanded CI, project docs (LICENSE, CONTRIBUTING, CODEOWNERS, SECURITY, CHANGELOG).
2. **API modernization** — FastAPI app, Pydantic models, config, logging, metrics, rate limiting, tests.
3. **Containerization & operations** — Dockerfile, docker-compose, migration runner, backup/restore scripts, release/rollback workflow, runbooks.
4. **Observability polish** — SLOs, alert examples, tracing hook, load-test baseline.

This design intentionally keeps the existing static-site scripts and data model unchanged while surrounding them with production-grade tooling and runtime behavior.
