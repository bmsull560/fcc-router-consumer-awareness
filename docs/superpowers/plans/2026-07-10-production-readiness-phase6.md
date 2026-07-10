# Phase 6: Architecture, Ownership, Release, and Upgrade Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Close the documentation and release-discipline gaps by adding an architecture/ownership doc, a release/upgrade runbook, updating contributor and README docs with new commands, and cutting the first versioned changelog entry.

**Architecture:** Keep documentation in Markdown under `docs/` and the repo root. Mirror existing styles: concise tables, copy-pasteable commands, and explicit file responsibilities. Avoid changing runtime code; this phase is docs-only.

**Tech Stack:** Markdown, GitHub Actions, semantic versioning.

---

## File Structure

| File | Responsibility |
|------|----------------|
| `docs/architecture.md` | System architecture, component map, data flow, ownership, and decision records. |
| `docs/runbooks/release-upgrade.md` | How to cut a release, write release notes, and upgrade a deployment. |
| `README.md` | Update command table and add links to architecture and runbooks. |
| `CONTRIBUTING.md` | Add `make audit`, `make e2e`, `make restore`, and security expectations. |
| `CHANGELOG.md` | Move completed work under a new `## [0.1.0]` section and refresh `[Unreleased]`. |
| `CODEOWNERS` | Optional refinement for docs, runbooks, and CI paths. |

---

### Task 1: Architecture and ownership document

**Files:**
- Create: `docs/architecture.md`

- [x] **Step 1: Create the architecture document**

Create `docs/architecture.md`:

```markdown
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
```

- [x] **Step 2: Verify the file renders**

Run: `make pre-commit`
Expected: Markdown/whitespace checks pass.

---

### Task 2: Release and upgrade runbook

**Files:**
- Create: `docs/runbooks/release-upgrade.md`

- [x] **Step 1: Create the release/upgrade runbook**

Create `docs/runbooks/release-upgrade.md`:

```markdown
# Release and Upgrade Runbook

## Versioning

This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

- `MAJOR` — incompatible API or schema changes requiring consumer action.
- `MINOR` — new features, endpoints, or schema additions that are backward compatible.
- `PATCH` — bug fixes, security patches, documentation corrections, or data refreshes.

## Cutting a release

1. **Ensure `main` is green.**
   All CI checks must pass on the commit you intend to tag.

2. **Update `CHANGELOG.md`.**
   Move items from `## [Unreleased]` into a new versioned section:
   ```markdown
   ## [0.1.1] - 2026-07-10
   ### Added
   - ...
   ### Fixed
   - ...
   ```

3. **Bump the version in `pyproject.toml`.**
   ```toml
   version = "0.1.1"
   ```

4. **Commit the changelog and version bump.**
   ```bash
   git add CHANGELOG.md pyproject.toml
   git commit -m "chore: release v0.1.1"
   ```

5. **Create and push a signed tag.**
   ```bash
   git tag -s v0.1.1 -m "Release v0.1.1"
   git push origin main v0.1.1
   ```

6. **Verify the release workflow.**
   The `.github/workflows/release.yml` workflow builds and pushes:
   - `ghcr.io/bmsull560/fcc-router-consumer-awareness:v0.1.1`
   - `ghcr.io/bmsull560/fcc-router-consumer-awareness:latest`

7. **Publish release notes.**
   Use the GitHub release page or a `RELEASE_NOTES.md` file to summarize:
   - Highlights
   - Breaking changes (if any)
   - Migration steps
   - Links to the relevant runbooks

## Upgrading a deployment

1. **Back up the existing database.**
   ```bash
   docker compose down
   python scripts/backup_db.py
   ```

2. **Pull the new image and run migrations.**
   Follow the [Deployment Runbook](./deployment.md).

3. **Verify health and metrics.**
   ```bash
   curl -f http://localhost:8000/healthz
   curl -f http://localhost:8000/ready
   curl -f http://localhost:8000/metrics
   ```

4. **Monitor SLOs.**
   Watch error rate and p99 latency for 15 minutes. If thresholds are breached, follow the [Rollback Runbook](./rollback.md).

## Rolling back

See the [Rollback Runbook](./rollback.md).
```

- [x] **Step 2: Link from README**

Add a "Release and upgrade" link in `README.md` near the CI section.

---

### Task 3: Update README and CONTRIBUTING

**Files:**
- Modify: `README.md`
- Modify: `CONTRIBUTING.md`

- [x] **Step 1: Update README command table**

In `README.md`, update the development commands table to include the new targets:

```markdown
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
```

- [x] **Step 2: Add architecture and runbook links to README**

After the "Scope and caveats" section, add:

```markdown
## Architecture and operations

- [Architecture and Ownership](./docs/architecture.md)
- [Deployment Runbook](./docs/runbooks/deployment.md)
- [Release and Upgrade Runbook](./docs/runbooks/release-upgrade.md)
- [Incident Response Runbook](./docs/runbooks/incident-response.md)
- [Rollback Runbook](./docs/runbooks/rollback.md)
- [Disaster Recovery Runbook](./docs/runbooks/disaster-recovery.md)
- [SLOs and Alert Examples](./docs/runbooks/slos-alerts.md)
- [Load-Testing Runbook](./docs/runbooks/load-testing.md)
```

- [x] **Step 3: Update CONTRIBUTING with new commands and security notes**

In `CONTRIBUTING.md`, update the development commands table:

```markdown
| Task | Command |
|---|---|
| Lint | `make lint` |
| Format | `make format` |
| Type check | `make type-check` |
| Run tests | `make test` |
| Run E2E tests | `make e2e` |
| Audit dependencies | `make audit` |
| Validate database | `make validate` |
| Build static site | `make build` |
| Run pre-commit hooks | `make pre-commit` |
```

Add a new section before "Security reporting":

```markdown
## Security and dependency hygiene

- Run `make audit` before opening a pull request.
- Do not commit secrets, API keys, or database files.
- Keep dependencies pinned with lower and upper bounds in `pyproject.toml`.
- If `pip-audit` reports a vulnerability, fix it in the same PR or document why it is a false positive.
```

- [x] **Step 4: Verify pre-commit still passes**

Run: `make pre-commit`
Expected: all hooks pass.

---

### Task 4: Update CHANGELOG

**Files:**
- Modify: `CHANGELOG.md`

- [x] **Step 1: Add a versioned release section**

Move the current `[Unreleased]` content into a new `## [0.1.0]` section. Keep the existing bullets, but group them under the appropriate headings. Example:

```markdown
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
- Operational runbooks under `docs/runbooks/` covering deployment, incident response, rollback, disaster recovery, SLOs/alerts, and load testing.
- `app/tracing.py` lightweight request tracing hook and `locustfile.py` load-test baseline.
- `tests/test_e2e.py` end-to-end tests against a real uvicorn server and `tests/test_integration_workflow.py` backup/restore/validate integration test.
- `make audit` and `make e2e` targets; dependency-audit and E2E jobs in CI.
- `docs/architecture.md` and `docs/runbooks/release-upgrade.md` documenting system architecture, ownership, release, and upgrade procedures.
- `tests/` covering HTML rendering, JSON export determinism, full site builds, API behavior, migrations, backups, restore, E2E, and integration workflows.
- `docs/database_README.md`, `docs/source-caveats.md`, `docs/architecture.md`, and planning docs under `docs/superpowers/`.
- `LICENSE` (CC0-1.0).
```

Use the actual project history; the bullets above are the consolidated set.

- [x] **Step 2: Update `pyproject.toml` version to 0.1.0**

Set:

```toml
version = "0.1.0"
```

(If it is already `0.1.0`, no change is needed.)

- [x] **Step 3: Verify pre-commit**

Run: `make pre-commit`
Expected: all hooks pass.

---

### Task 5: Optional CODEOWNERS refinement

**Files:**
- Modify: `CODEOWNERS`

- [x] **Step 1: Add path-specific owners**

Update `CODEOWNERS` to:

```text
# Default reviewers for the whole repository
* @bmsull560

# Operational and deployment docs
/docs/runbooks/ @bmsull560
/.github/workflows/ @bmsull560

# Database schema and migrations
/migrations/ @bmsull560
/data/ @bmsull560
```

- [x] **Step 2: Verify**

Run: `make pre-commit`
Expected: all hooks pass.

---

## Self-Review

- **Spec coverage:** Architecture/ownership (Task 1), release/upgrade (Task 2), README/CONTRIBUTING updates (Task 3), changelog/version (Task 4), and optional CODEOWNERS refinement (Task 5) are all covered.
- **Placeholder scan:** No TBD/TODO placeholders; every step contains exact content.
- **Type consistency:** Not applicable for a docs-only phase; no new code types are introduced.

---

## Final State

All tasks in this plan were implemented and verified.

### Completed deliverables

- `docs/architecture.md` — system architecture, component ownership table, data flow, security defaults, and decision records.
- `docs/runbooks/release-upgrade.md` — semantic-versioning policy, release checklist, upgrade steps, and rollback reference.
- `README.md` — updated command table (`make e2e`, `make audit`, `make backup`, `make restore BACKUP=...`) and new "Architecture and operations" link section.
- `CONTRIBUTING.md` — added new commands table and a "Security and dependency hygiene" section.
- `CHANGELOG.md` — added `## [0.1.0] - 2026-07-10` release section and cleared `[Unreleased]`.
- `CODEOWNERS` — added path-specific ownership for runbooks, workflows, migrations, and data.
- `pyproject.toml` — version remains `0.1.0`.

### Verified gates

- `make pre-commit` ✅
- `make validate` ✅
- `make build` ✅

### Notes

- This phase is documentation-only; no runtime code was changed.
- The `0.1.0` release date should be updated to the actual release date when the tag is cut.
