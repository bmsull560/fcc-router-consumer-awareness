# Phase 2 — Core FastAPI API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the stdlib `http.server` JSON API with a production-oriented FastAPI application that exposes the same endpoints plus a readiness probe, while keeping the existing static-site generator untouched.

**Architecture:** FastAPI dependency injection provides a per-request SQLite connection. Pydantic models shape response payloads. A `/ready` endpoint verifies DB accessibility. Configuration is env-driven via Pydantic Settings. Structured logging, metrics, and rate limiting are intentionally out of scope for this plan (Phase 2b).

**Tech Stack:** Python 3.10+, FastAPI, Uvicorn, Gunicorn, Pydantic Settings, SQLite3, pytest.

---

## File structure

| File | Responsibility |
|---|---|
| `pyproject.toml` | Adds runtime dependencies (`fastapi`, `uvicorn`, `gunicorn`, `pydantic-settings`, `httpx`) |
| `app/config.py` | Pydantic Settings for env-driven configuration |
| `app/db.py` | FastAPI dependency that yields a SQLite connection per request |
| `app/models.py` | Pydantic response models for each endpoint |
| `app/api.py` | FastAPI app, lifespan, middleware, exception handlers, and endpoints |
| `tests/test_api.py` | Integration tests using FastAPI `TestClient` |
| `Makefile` | Adds `api` target to run the FastAPI dev server |
| `README.md` | Documents the new FastAPI application and `make api` command |

---

## Task 1: Add runtime dependencies

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add runtime dependencies**

Add these packages to `[project.dependencies]` in `pyproject.toml`:

```toml
dependencies = [
    "fastapi>=0.111.0,<1",
    "uvicorn[standard]>=0.30.0,<1",
    "gunicorn>=22.0,<23",
    "pydantic-settings>=2.3.0,<3",
    "httpx>=0.27.0,<1",
]
```

- [ ] **Step 2: Reinstall the project in editable mode**

Run:

```bash
.venv/Scripts/python -m pip install -e ".[dev]"
```

Expected: package reinstalls with new runtime dependencies.

---

## Task 2: Create `app/config.py`

**Files:**
- Create: `app/config.py`

- [ ] **Step 1: Write `app/config.py`**

```python
"""Application configuration via Pydantic Settings."""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """Environment-driven settings.

    Variables are read with the ``FCC_`` prefix by default, e.g.
    ``FCC_DB_PATH``, ``FCC_CORS_ORIGINS``.
    """

    app_name: str = "FCC Router Consumer Awareness API"
    debug: bool = False
    db_path: Path = ROOT / "data" / "fcc_router_consumer_awareness.db"
    cors_origins: list[str] = []
    log_level: str = "INFO"

    model_config = {"env_prefix": "FCC_"}


def get_settings() -> Settings:
    """Return a cached-ish Settings instance."""
    return Settings()
```

---

## Task 3: Create `app/db.py`

**Files:**
- Create: `app/db.py`

- [ ] **Step 1: Write `app/db.py`**

```python
"""SQLite database dependency for FastAPI."""
from __future__ import annotations

import sqlite3
from collections.abc import Generator

from app.config import get_settings


def get_db_conn() -> Generator[sqlite3.Connection, None, None]:
    """Yield a SQLite connection and close it after the request."""
    settings = get_settings()
    conn = sqlite3.connect(str(settings.db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
```

---

## Task 4: Create `app/models.py`

**Files:**
- Create: `app/models.py`

- [ ] **Step 1: Write `app/models.py`**

```python
"""Pydantic response models for the FastAPI application."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ok: bool


class ReadyResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    status: str


class StatusResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    headline: str | None = None
    continued_use_note: str | None = None
    update_note: str | None = None
    verification_note: str | None = None
    current_as_of: str | None = None


class FAQResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    category: str | None = None
    question: str | None = None
    answer_short: str | None = None
    answer_long: str | None = None
    source_urls: str | None = None


class TimelineResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    event_date: str | None = None
    title: str | None = None
    event_type: str | None = None
    summary: str | None = None
    consumer_impact: str | None = None
    source_url: str | None = None
    source_title: str | None = None


class AlertResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    severity: str | None = None
    title: str | None = None
    body: str | None = None
    cta_label: str | None = None
    cta_url: str | None = None


class SourceResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    source_key: str | None = None
    title: str | None = None
    url: str | None = None
    publication_date: str | None = None
    source_type: str | None = None
    summary: str | None = None


class SearchResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    table_name: str | None = None
    row_id: int | None = None
    title: str | None = None
    snippet: str | None = None
```

---

## Task 5: Create `app/api.py`

**Files:**
- Create: `app/api.py`

- [ ] **Step 1: Write `app/api.py`**

```python
"""FastAPI application for the FCC router awareness dataset."""
from __future__ import annotations

import sqlite3
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.db import get_db_conn
from app.models import (
    AlertResponse,
    FAQResponse,
    HealthResponse,
    ReadyResponse,
    SearchResult,
    SourceResponse,
    StatusResponse,
    TimelineResponse,
)


def _rows_as_dicts(cursor: sqlite3.Cursor) -> list[dict[str, object]]:
    columns = [d[0] for d in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if not settings.db_path.exists():
        raise RuntimeError(f"Database not found: {settings.db_path}")
    yield


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    trace_id = uuid.uuid4().hex[:12]
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "trace_id": trace_id},
    )


@app.get("/healthz", response_model=HealthResponse)
def healthz():
    return {"ok": True}


@app.get("/ready", response_model=ReadyResponse)
def ready(db: sqlite3.Connection = Depends(get_db_conn)):
    try:
        db.execute("SELECT 1")
        return {"status": "ok"}
    except sqlite3.Error as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@app.get("/api/status", response_model=list[StatusResponse])
def get_status(db: sqlite3.Connection = Depends(get_db_conn)):
    cursor = db.execute("SELECT * FROM vw_current_consumer_status")
    return _rows_as_dicts(cursor)


@app.get("/api/faqs", response_model=list[FAQResponse])
def get_faqs(db: sqlite3.Connection = Depends(get_db_conn)):
    cursor = db.execute(
        "SELECT * FROM vw_public_faqs ORDER BY category, question"
    )
    return _rows_as_dicts(cursor)


@app.get("/api/timeline", response_model=list[TimelineResponse])
def get_timeline(db: sqlite3.Connection = Depends(get_db_conn)):
    cursor = db.execute(
        "SELECT * FROM vw_router_timeline ORDER BY event_date DESC"
    )
    return _rows_as_dicts(cursor)


@app.get("/api/alerts", response_model=list[AlertResponse])
def get_alerts(db: sqlite3.Connection = Depends(get_db_conn)):
    cursor = db.execute(
        """
        SELECT severity, title, body, cta_label, cta_url
        FROM alerts
        WHERE active = 1
        ORDER BY alert_id
        """
    )
    return _rows_as_dicts(cursor)


@app.get("/api/sources", response_model=list[SourceResponse])
def get_sources(db: sqlite3.Connection = Depends(get_db_conn)):
    cursor = db.execute(
        "SELECT * FROM vw_primary_sources ORDER BY publication_date DESC, source_key DESC"
    )
    return _rows_as_dicts(cursor)


@app.get("/api/search", response_model=list[SearchResult])
def search(
    q: str = Query(..., min_length=1, description="Search query"),
    db: sqlite3.Connection = Depends(get_db_conn),
):
    cursor = db.execute(
        """
        SELECT
            table_name,
            row_id,
            title,
            snippet(search_index, 3, '<mark>', '</mark>', '...', 16) AS snippet
        FROM search_index
        WHERE search_index MATCH ?
        LIMIT 20
        """,
        (q,),
    )
    return _rows_as_dicts(cursor)
```

---

## Task 6: Create `tests/test_api.py`

**Files:**
- Create: `tests/test_api.py`

- [ ] **Step 1: Write `tests/test_api.py`**

```python
"""Integration tests for the FastAPI application."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api import app


@pytest.fixture
def client():
    return TestClient(app)


def test_healthz(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_ready(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_get_status(client):
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "headline" in data[0]


def test_get_faqs(client):
    response = client.get("/api/faqs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "question" in data[0]


def test_get_timeline(client):
    response = client.get("/api/timeline")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "event_date" in data[0]


def test_get_alerts(client):
    response = client.get("/api/alerts")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_sources(client):
    response = client.get("/api/sources")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "title" in data[0]


def test_search_requires_q(client):
    response = client.get("/api/search")
    assert response.status_code == 422


def test_search_returns_results(client):
    response = client.get("/api/search", params={"q": "router"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_search_rejects_short_q(client):
    response = client.get("/api/search", params={"q": ""})
    assert response.status_code == 422


def test_security_headers_present(client):
    response = client.get("/healthz")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"


def test_not_found(client):
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert "error" in response.json()
```

---

## Task 7: Update `Makefile` and `README.md`

**Files:**
- Modify: `Makefile`
- Modify: `README.md`

- [ ] **Step 1: Add an `api` target to `Makefile`**

Add `api` to the `.PHONY` line and add the target:

```makefile
.PHONY: help install lint format format-check type-check test validate build clean pre-commit api

# ... existing targets ...

api: ## Run the FastAPI development server with auto-reload
	$(BIN)/uvicorn app.api:app --reload
```

- [ ] **Step 2: Update `README.md` API section**

Replace the existing "Run the local JSON API" section with:

```markdown
## Run the local JSON API

```bash
make api
```

Open these endpoints:

```text
http://localhost:8000/healthz
http://localhost:8000/ready
http://localhost:8000/api/status
http://localhost:8000/api/faqs
http://localhost:8000/api/timeline
http://localhost:8000/api/alerts
http://localhost:8000/api/sources
http://localhost:8000/api/search?q=firmware
```
```

---

## Task 8: Run lint, type-check, and tests

**Files:**
- Modify: any `.py` files that fail lint/type-check

- [ ] **Step 1: Run linting and formatting**

```bash
.venv/Scripts/ruff format .
.venv/Scripts/ruff check . --fix
```

Expected: `ruff check .` exits 0.

- [ ] **Step 2: Run type checking**

```bash
.venv/Scripts/mypy app scripts tests
```

Expected: no issues.

- [ ] **Step 3: Run tests**

```bash
.venv/Scripts/pytest
```

Expected: all tests pass and coverage is at least 60%.

---

## Spec coverage check

| Design requirement | Task that implements it |
|---|---|
| Replace stdlib server with FastAPI | Task 5 (`app/api.py`) |
| Pydantic models and settings | Tasks 2, 4 (`app/config.py`, `app/models.py`) |
| Per-request SQLite connection | Task 3 (`app/db.py`) |
| Health/readiness probes | Task 5 (`/healthz`, `/ready`) |
| Input validation | Task 5 (`Query(..., min_length=1)`) |
| Security headers | Task 5 (`add_security_headers` middleware) |
| CORS configurable | Task 5 (conditional `CORSMiddleware`) |
| Integration tests | Task 6 (`tests/test_api.py`) |
| Documented run command | Task 7 (`Makefile`, `README.md`) |

## Placeholder scan

- No `TBD`, `TODO`, or `implement later` strings.
- Every created file has complete content.
- Every command has an expected outcome.
- Type and function names are consistent across tasks.

## Out of scope for this plan

- Structured logging (Phase 2b)
- Prometheus metrics endpoint `/metrics` (Phase 2b)
- Rate limiting on `/api/search` (Phase 2b)
- Containerization and release workflow (Phase 3)
- Versioned database migrations (Phase 3)
- Operational runbooks (Phase 3)
