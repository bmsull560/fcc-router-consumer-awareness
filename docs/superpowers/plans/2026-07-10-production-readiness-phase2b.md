# Phase 2b: Observability & Rate Limiting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add structured JSON logging, a Prometheus `/metrics` endpoint, and a 30 requests/minute rate limit on `/api/search` to the FastAPI application.

**Architecture:** Use `structlog` for configurable JSON/console logging, a FastAPI middleware for request/access logs and trace IDs, `prometheus-fastapi-instrumentator` for HTTP metrics, and `slowapi` for in-memory per-IP rate limiting on the search endpoint. Tests cover the new endpoints and rate-limit behavior.

**Tech Stack:** Python 3.10+, FastAPI, structlog, prometheus-fastapi-instrumentator, slowapi, pytest.

---

## File Structure

| File | Responsibility |
|------|----------------|
| `pyproject.toml` | Add `structlog`, `prometheus-fastapi-instrumentator`, and `slowapi` runtime dependencies. |
| `app/logging.py` | New module: configure structlog for JSON or console output, and configure stdlib logging to route through structlog. |
| `app/api.py` | Wire logging config, request logging middleware, trace IDs, Prometheus instrumentation, and slowapi rate limiting. |
| `tests/test_api.py` | Tests for `/metrics`, `X-Trace-ID` header, and `/api/search` rate limiting. |
| `README.md` | Document `/metrics` and the search rate limit. |

---

### Task 1: Add runtime dependencies

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add the three runtime dependencies**

Add to the `dependencies` list in `pyproject.toml` (order alphabetically):

```toml
dependencies = [
    "fastapi>=0.111.0,<1",
    "uvicorn[standard]>=0.30.0,<1",
    "gunicorn>=22.0,<23",
    "prometheus-fastapi-instrumentator>=7.0.0,<9",
    "pydantic-settings>=2.3.0,<3",
    "slowapi>=0.1.9,<1",
    "structlog>=24.1.0,<27",
    "httpx>=0.27.0,<1",
]
```

- [ ] **Step 2: Install the updated package**

```bash
.venv/Scripts/pip install -e ".[dev]"
```

Expected: all three packages install without error.

- [ ] **Step 3: Verify the imports**

```bash
.venv/Scripts/python -c "import structlog; import prometheus_fastapi_instrumentator; import slowapi; print('imports ok')"
```

Expected output: `imports ok`

---

### Task 2: Create the logging configuration module

**Files:**
- Create: `app/logging.py`

- [ ] **Step 1: Write `app/logging.py`**

```python
"""Structured logging configuration using structlog."""

from __future__ import annotations

import logging.config
from typing import Any

import structlog
from structlog.typing import Processor


def configure_logging(log_level: str, json_format: bool = True) -> None:
    """Configure structlog and stdlib logging.

    When ``json_format`` is True, logs are emitted as JSON. When False, logs are
    emitted in a human-readable console format suitable for local development.
    """
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.ExtraAdder(),
        structlog.processors.format_exc_info,
    ]

    formatter_processor: Processor = (
        structlog.processors.JSONRenderer()
        if json_format
        else structlog.dev.ConsoleRenderer(colors=True)
    )

    structlog.configure(
        processors=shared_processors + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": formatter_processor,
                    "foreign_pre_chain": shared_processors,
                },
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                },
            },
            "loggers": {
                "": {"handlers": ["default"], "level": log_level},
            },
        }
    )


def get_logger(*args: Any, **kwargs: Any) -> structlog.stdlib.BoundLogger:
    """Return a structlog logger."""
    return structlog.get_logger(*args, **kwargs)
```

- [ ] **Step 2: Smoke-test the logging module**

```bash
.venv/Scripts/python -c "from app.logging import configure_logging; configure_logging('INFO', json_format=True); print('logging configured')"
```

Expected output: `logging configured`

---

### Task 3: Wire structured logging and trace IDs into the API

**Files:**
- Modify: `app/api.py`

- [ ] **Step 1: Add imports**

Add to the top of `app/api.py`:

```python
import time

from app.logging import configure_logging, get_logger
```

- [ ] **Step 2: Configure logging on startup**

Update the `lifespan` function to call `configure_logging`:

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level, json_format=not settings.debug)
    if not settings.db_path.exists():
        raise RuntimeError(f"Database not found: {settings.db_path}")
    yield
```

- [ ] **Step 3: Add request logging middleware**

Add this middleware **after** `add_security_headers`:

```python
@app.middleware("http")
async def log_requests(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    trace_id = uuid.uuid4().hex[:12]
    request.state.trace_id = trace_id
    logger = get_logger()
    start = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        logger.error(
            "request_failed",
            method=request.method,
            path=request.url.path,
            trace_id=trace_id,
        )
        raise

    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round(duration_ms, 3),
        trace_id=trace_id,
    )
    response.headers["X-Trace-ID"] = trace_id
    return response
```

- [ ] **Step 4: Add a secure JSON response helper**

Add this helper after `_rows_as_dicts` so exception handlers can attach security headers and a trace ID consistently:

```python
def _secure_json_response(
    request: Request,
    status_code: int,
    content: dict[str, object],
    extra_headers: dict[str, str] | None = None,
    trace_id: str | None = None,
) -> JSONResponse:
    """Return a JSON response with security headers and a trace ID."""
    resolved_trace_id: str
    if trace_id is not None:
        resolved_trace_id = trace_id
    else:
        resolved_trace_id = getattr(request.state, "trace_id", uuid.uuid4().hex[:12])
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-Trace-ID": resolved_trace_id,
    }
    if extra_headers:
        headers.update(extra_headers)
    return JSONResponse(status_code=status_code, content=content, headers=headers)
```

- [ ] **Step 5: Include the trace ID in unhandled error responses**

Update the unhandled exception handler to use the helper:

```python
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    trace_id = getattr(request.state, "trace_id", uuid.uuid4().hex[:12])
    get_logger().error(
        "unhandled_exception",
        trace_id=trace_id,
        exc_info=exc,
    )
    return _secure_json_response(
        request,
        500,
        {"error": "Internal server error", "trace_id": trace_id},
        trace_id=trace_id,
    )
```

- [ ] **Step 6: Run the existing API tests**

```bash
.venv/Scripts/pytest tests/test_api.py -v
```

Expected: all existing tests still pass.

---

### Task 4: Add the Prometheus `/metrics` endpoint

**Files:**
- Modify: `app/api.py`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Instrument the application**

Add the import near the top of `app/api.py`:

```python
from prometheus_fastapi_instrumentator import Instrumentator
```

Add the instrumentation **after** the middleware definitions and **before** the route definitions:

```python
Instrumentator().instrument(app).expose(app)
```

- [ ] **Step 2: Add a test for `/metrics`**

Add to `tests/test_api.py`:

```python
def test_metrics_endpoint(client):
    # Prime at least one request so default latency metrics are present.
    client.get("/healthz")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_request_duration_seconds" in response.text
```

- [ ] **Step 3: Run the metrics test**

```bash
.venv/Scripts/pytest tests/test_api.py::test_metrics_endpoint -v
```

Expected: PASS.

---

### Task 5: Add rate limiting to `/api/search`

**Files:**
- Modify: `app/api.py`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Import slowapi components**

Add to `app/api.py`:

```python
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
```

- [ ] **Step 2: Create and attach the limiter and exception handler**

After the `app = FastAPI(...)` block and **before** route definitions, add:

```python
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
```

Also add a custom `RateLimitExceeded` exception handler (do not rely on slowapi's private `_rate_limit_exceeded_handler`):

```python
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    trace_id = getattr(request.state, "trace_id", uuid.uuid4().hex[:12])
    get_logger().warning(
        "rate_limit_exceeded",
        method=request.method,
        path=request.url.path,
        trace_id=trace_id,
    )
    return _secure_json_response(
        request,
        429,
        {"error": "Rate limit exceeded"},
        extra_headers={"Retry-After": "60"},
        trace_id=trace_id,
    )
```

- [ ] **Step 3: Apply the rate limit to `/api/search`**

Update the search endpoint signature and add the decorator:

```python
@app.get("/api/search", response_model=list[SearchResult])
@limiter.limit("30/minute")
def search(
    request: Request,
    q: str = Query(..., min_length=1, description="Search query"),
    db: sqlite3.Connection = Depends(get_db_conn),
) -> list[dict[str, object]]:
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

The `request: Request` parameter is required by `slowapi` and is injected automatically by FastAPI.

- [ ] **Step 4: Expose `limiter` at module level for tests**

Ensure the `limiter` variable is defined at module scope so tests can import it. No additional change is needed if Step 2 placed it at module scope.

- [ ] **Step 5: Add rate-limit tests**

Add to `tests/test_api.py`:

```python
from app.api import limiter


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    limiter.reset()
    yield


def test_search_rate_limit(client):
    # The first 30 requests within a minute are allowed.
    for _ in range(30):
        response = client.get("/api/search", params={"q": "router"})
        assert response.status_code == 200, response.text

    # The 31st request is rate limited.
    response = client.get("/api/search", params={"q": "router"})
    assert response.status_code == 429
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "X-Trace-ID" in response.headers
    assert response.headers.get("Retry-After") == "60"


def test_search_rate_limit_resets_after_reset(client):
    for _ in range(5):
        response = client.get("/api/search", params={"q": "router"})
        assert response.status_code == 200
    limiter.reset()
    response = client.get("/api/search", params={"q": "router"})
    assert response.status_code == 200
```

- [ ] **Step 6: Run the search and rate-limit tests**

```bash
.venv/Scripts/pytest tests/test_api.py -v
```

Expected: all tests pass.

---

### Task 6: Update README documentation

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add `/metrics` to the endpoint list**

In the "Open these endpoints" block, add:

```text
http://localhost:8000/metrics
```

- [ ] **Step 2: Document the rate limit**

After the endpoint list, add a short note:

```markdown
## Rate limits

The `/api/search` endpoint is rate-limited to 30 requests per minute per client IP.
```

---

### Task 7: Run the full validation suite

**Files:**
- None

- [ ] **Step 1: Run linting, type checking, and tests**

```bash
.venv/Scripts/ruff check .
.venv/Scripts/mypy app scripts tests
.venv/Scripts/pytest
```

Expected:
- `ruff check .` exits 0.
- `mypy app scripts tests` exits 0.
- `pytest` exits 0 with all tests passing.

- [ ] **Step 2: Run build and validation targets**

```bash
make validate
make build
```

Expected: both complete successfully.

- [ ] **Step 3: Run pre-commit hooks**

```bash
make pre-commit
```

Expected: pre-commit passes.

---

## Self-Review

- **Spec coverage:** Structured logging (Task 2–3), Prometheus metrics (Task 4), rate limiting (Task 5), documentation (Task 6), and full validation (Task 7) are all covered.
- **Placeholder scan:** No TBD/TODO placeholders; every step contains exact code or exact commands.
- **Type consistency:** `configure_logging` signature is reused in lifespan; `request: Request` is added consistently to the search endpoint; `limiter` is module-scoped and imported in tests.
