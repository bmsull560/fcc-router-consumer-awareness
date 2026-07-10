# Phase 4: SLOs, Alert Examples, Tracing Hook, and Load-Test Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Define and document service-level objectives and example alerts, add a lightweight request-tracing hook to the FastAPI app, and establish a reproducible load-test baseline.

**Architecture:** Keep changes minimal and production-aligned. SLOs and alerts live as Markdown runbooks with copy-pasteable Prometheus rules. The tracing hook binds a per-request trace ID into structlog context vars and reads/writes trace IDs via HTTP headers, without adding a heavy vendor dependency. Load testing uses Locust as a dev dependency with a small `locustfile.py` targeting the public read endpoints.

**Tech Stack:** Python 3.10+, FastAPI, structlog, Locust, Prometheus.

---

## File Structure

| File | Responsibility |
|------|----------------|
| `docs/runbooks/slos-alerts.md` | Defined SLOs, SLIs, and example Prometheus alerting rules. |
| `app/tracing.py` | Trace ID generation, header propagation, and structlog context binding. |
| `app/api.py` | Wire the tracing middleware; ensure all logs include trace_id. |
| `app/logging.py` | Add trace_id processor to shared structlog processors. |
| `locustfile.py` | Locust load-test scenario for public API endpoints. |
| `docs/runbooks/load-testing.md` | How to run load tests and interpret baseline numbers. |
| `pyproject.toml` | Add `locust>=2.29.0,<3` to dev dependencies. |
| `tests/test_api.py` | Add tests for trace-id header propagation and log context. |

---

### Task 1: SLOs and alert examples

**Files:**
- Create: `docs/runbooks/slos-alerts.md`

- [x] **Step 1: Create the SLO/alert runbook**

Create `docs/runbooks/slos-alerts.md`:

```markdown
# SLOs and Alert Examples

## Service-Level Objectives

| SLO | Target | SLI | Measurement |
|-----|--------|-----|-------------|
| Availability | 99.9% over 30 days | `/healthz` and `/ready` success rate | Prometheus `up` and `http_request_duration_seconds_count{status=~"2..|3.."}` |
| Latency p99 | < 500 ms | Response time for `/api/*` | Prometheus histogram `http_request_duration_seconds_bucket{le="0.5"}` |
| Error rate | < 0.1% | 5xx responses across all routes | Prometheus `rate(http_request_duration_seconds_count{status=~"5.."}[5m])` |
| Rate-limit fairness | < 1% of legitimate requests throttled | 429 responses on `/api/search` | Prometheus `rate(http_request_duration_seconds_count{status="429"}[5m])` |

## Prometheus alerting rules

Save these as `prometheus-rules.yml` in your monitoring repository:

```yaml
groups:
  - name: fcc-router-consumer-awareness
    rules:
      - alert: FCCRouterAPIDown
        expr: up{job="fcc-router-consumer-awareness"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "FCC Router Consumer Awareness API is down"

      - alert: FCCRouterAPIHighErrorRate
        expr: |
          sum(rate(http_request_duration_seconds_count{status=~"5.."}[5m]))
          /
          sum(rate(http_request_duration_seconds_count[5m])) > 0.001
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High 5xx error rate on FCC Router API"

      - alert: FCCRouterAPIHighLatency
        expr: |
          histogram_quantile(0.99,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
          ) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "FCC Router API p99 latency exceeds 500 ms"

      - alert: FCCRouterAPIDatabaseNotReady
        expr: ready_status{job="fcc-router-consumer-awareness"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "FCC Router API database readiness check is failing"
```

## Runbook links

- Incident response: [./incident-response.md](./incident-response.md)
- Rollback: [./rollback.md](./rollback.md)
- Disaster recovery: [./disaster-recovery.md](./disaster-recovery.md)
```

- [x] **Step 2: Link the runbook from the incident-response runbook**

Modify `docs/runbooks/incident-response.md` to add a "Monitoring and SLOs" section referencing `slos-alerts.md`.

---

### Task 2: Tracing hook

**Files:**
- Create: `app/tracing.py`
- Modify: `app/api.py` (middleware section)
- Modify: `app/logging.py`

- [x] **Step 1: Create the tracing module**

Create `app/tracing.py`:

```python
"""Lightweight request tracing helpers.

This module provides a minimal tracing hook that:

- Generates or reuses a trace ID for every incoming request.
- Binds the trace ID to structlog context vars so every log line in the
  request scope includes it.
- Exposes the trace ID via the ``X-Trace-ID`` response header.

It is intentionally dependency-free. Teams that need full distributed tracing
can replace the hook with OpenTelemetry instrumentation without changing the
middleware interface.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request
from starlette.responses import Response
import structlog.contextvars

TRACE_ID_HEADER = "X-Trace-ID"


def generate_trace_id() -> str:
    """Return a 12-character hex trace ID."""
    return uuid.uuid4().hex[:12]


def get_trace_id(request: Request) -> str:
    """Return the existing trace ID from headers or generate a new one."""
    header_value = request.headers.get(TRACE_ID_HEADER)
    if header_value:
        return header_value.strip()[:32]
    return generate_trace_id()


async def tracing_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Bind a trace ID to the request and log context."""
    trace_id = get_trace_id(request)
    request.state.trace_id = trace_id
    structlog.contextvars.bind_contextvars(trace_id=trace_id)
    try:
        response = await call_next(request)
        response.headers[TRACE_ID_HEADER] = trace_id
        return response
    finally:
        structlog.contextvars.unbind_contextvars("trace_id")
```

- [x] **Step 2: Add trace_id to the shared logging processors**

Modify `app/logging.py` shared_processors to include the trace_id:

```python
shared_processors: list[Processor] = [
    structlog.contextvars.merge_contextvars,
    structlog.processors.add_log_level,
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.stdlib.ExtraAdder(),
    structlog.processors.format_exc_info,
]
```

`merge_contextvars` is already present, so `trace_id` bound by the middleware will automatically appear in every log record. No further code change is needed in `app/logging.py`, but add a docstring note explaining this.

- [x] **Step 3: Wire the tracing middleware into the FastAPI app**

Modify `app/api.py`:

1. Import the middleware near the top:

```python
from app.tracing import tracing_middleware
```

2. Replace the existing `log_requests` middleware's trace-id generation with the middleware. The simplest path is to add `tracing_middleware` before `log_requests` and have `log_requests` read `request.state.trace_id`:

```python
app.middleware("http")(tracing_middleware)
```

Then update `log_requests` to remove its own `uuid.uuid4().hex[:12]` generation and rely on `request.state.trace_id`.

Expected `app/api.py` middleware wiring after the change:

```python
@app.middleware("http")
async def log_requests(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    trace_id = getattr(request.state, "trace_id", uuid.uuid4().hex[:12])
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
    return response
```

- [x] **Step 4: Add tests for tracing behavior**

Add to `tests/test_api.py`:

```python
def test_trace_id_header_is_returned(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert "X-Trace-ID" in response.headers
    assert len(response.headers["X-Trace-ID"]) == 12


def test_trace_id_header_is_propagated(client):
    trace_id = "abc123def456"
    response = client.get("/healthz", headers={"X-Trace-ID": trace_id})
    assert response.headers["X-Trace-ID"] == trace_id
```

- [x] **Step 5: Run API tests**

Run: `.venv/Scripts/pytest tests/test_api.py -v`
Expected: all tests pass.

---

### Task 3: Load-test baseline

**Files:**
- Modify: `pyproject.toml`
- Create: `locustfile.py`
- Create: `docs/runbooks/load-testing.md`

- [x] **Step 1: Add Locust as a dev dependency**

Modify `pyproject.toml` dev dependencies:

```toml
dev = [
    "ruff>=0.5.0,<1",
    "mypy>=1.10.0,<3",
    "pytest>=8.2.0,<10",
    "pytest-cov>=5.0.0,<7",
    "pre-commit>=3.7.0,<5",
    "pip-audit>=2.7.0,<3",
    "locust>=2.29.0,<3",
]
```

- [x] **Step 2: Install the updated dev dependencies**

Run: `.venv/Scripts/pip install -e ".[dev]"`
Expected: locust is installed.

- [x] **Step 3: Create the Locust file**

Create `locustfile.py`:

```python
"""Load-test scenario for the FCC Router Consumer Awareness API."""

from __future__ import annotations

from locust import HttpUser, between, task


class ApiUser(HttpUser):
    """Simulates a reader browsing the public API."""

    wait_time = between(1, 3)

    @task(5)
    def get_status(self) -> None:
        self.client.get("/api/status")

    @task(4)
    def get_faqs(self) -> None:
        self.client.get("/api/faqs")

    @task(3)
    def get_timeline(self) -> None:
        self.client.get("/api/timeline")

    @task(2)
    def get_sources(self) -> None:
        self.client.get("/api/sources")

    @task(1)
    def search(self) -> None:
        self.client.get("/api/search?q=router")

    @task(1)
    def healthz(self) -> None:
        self.client.get("/healthz")
```

- [x] **Step 4: Create the load-testing runbook**

Create `docs/runbooks/load-testing.md`:

```markdown
# Load-Testing Runbook

## Baseline target

Run on a host comparable to the production deployment (CPU/memory class).

| Metric | Target |
|--------|--------|
| RPS | >= 100 requests/second |
| p99 latency | < 500 ms |
| Error rate | < 0.1% |
| CPU utilization | < 80% at target RPS |

## Run locally

1. Start the API in production-like mode:
   ```bash
   make api
   ```

2. Run Locust:
   ```bash
   .venv/Scripts/locust -f locustfile.py --host http://localhost:8000 -u 50 -r 10 -t 60s --headless
   ```

3. Capture the output (RPS, p99, failures) and record it in this runbook or in a release note.

## Interpretation

- If p99 latency exceeds 500 ms, check the SQLite query plans and consider adding indexes or caching.
- If error rate is > 0.1%, check `unhandled_exception` logs by `trace_id`.
- If `/api/search` returns many 429s, tune the rate limit or add more workers.
```

- [x] **Step 5: Verify Locust can parse the file**

Run: `.venv/Scripts/locust -f locustfile.py --help`
Expected: locust starts without import errors and shows help.

---

### Task 4: Verification

**Files:**
- None

- [x] **Step 1: Run linting, type checking, and tests**

```bash
.venv/Scripts/ruff check .
.venv/Scripts/mypy app scripts tests
.venv/Scripts/pytest --cov-fail-under=60
```

Expected:
- `ruff check .` exits 0.
- `mypy app scripts tests` exits 0.
- `pytest` exits 0 with all tests passing and coverage >= 60%.

- [x] **Step 2: Run build and validation targets**

```bash
make validate
make build
make pre-commit
```

Expected: all complete successfully.

- [x] **Step 3: Quick manual load-test smoke check (optional)**

If the API is running locally:

```bash
.venv/Scripts/locust -f locustfile.py --host http://localhost:8000 -u 5 -r 2 -t 10s --headless
```

Expected: no import errors and the test runs to completion. Actual throughput numbers depend on the local machine.

---

## Self-Review

- **Spec coverage:** SLOs/alerts (Task 1), tracing hook (Task 2), load-test baseline (Task 3), and verification (Task 4) are all covered.
- **Placeholder scan:** No TBD/TODO placeholders; every step contains exact code or exact commands.
- **Type consistency:** `trace_id` is consistently a string, passed via `request.state.trace_id` and the `X-Trace-ID` header.

---

## Final State

All tasks in this plan were implemented and verified.

### Verified gates

- `ruff check .` ✅
- `mypy app scripts tests` ✅ (22 files)
- `pytest --cov-fail-under=60` ✅ 59 passed, ~85% coverage
- `make validate` ✅
- `make build` ✅
- `make pre-commit` ✅
- `locust -f locustfile.py --help` ✅ parses without import errors

### Notes

- The Locust help output emits a harmless greenlet finalization message on Windows exit; this is not a functional failure.
- Actual load-test numbers must be collected on a production-class host with the API running and a real database. The baseline targets are documented in `docs/runbooks/load-testing.md`.
