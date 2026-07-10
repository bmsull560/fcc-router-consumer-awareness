# Phase 5: Integration/E2E Tests and Dependency Scanning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add true end-to-end API tests that exercise a running server, add a dependency-security audit target to the local workflow, and wire both into CI.

**Architecture:** Use `subprocess` to start `uvicorn` bound to an ephemeral port for E2E tests, then use `httpx` (already a project dependency) to hit real HTTP endpoints. Add `make audit` and `make e2e` targets and a matching CI job so the local and automated workflows stay identical.

**Tech Stack:** Python 3.10+, pytest, httpx, uvicorn, pip-audit, GitHub Actions.

---

## File Structure

| File | Responsibility |
|------|----------------|
| `tests/test_e2e.py` | End-to-end tests that spin up the real API server and make HTTP requests. |
| `tests/test_integration_workflow.py` | Integration test for the backup/restore/validate workflow. |
| `Makefile` | Add `audit` and `e2e` targets. |
| `.github/workflows/ci.yml` | Add `e2e` and `audit` jobs; `audit` already exists but may need alignment with the Makefile target. |

---

### Task 1: End-to-end API tests

**Files:**
- Create: `tests/test_e2e.py`

- [x] **Step 1: Create the E2E test module**

Create `tests/test_e2e.py`:

```python
"""End-to-end tests that start a real uvicorn server and call it over HTTP."""

from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_server(url: str, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            response = httpx.get(url, timeout=1.0)
            if response.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(0.2)
    raise RuntimeError(f"Server did not become ready at {url}")


@pytest.fixture(scope="module")
def server_url():
    """Start the API on a free port and yield its base URL."""
    port = _find_free_port()
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.api:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        _wait_for_server(f"{url}/healthz")
        yield url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


def test_e2e_healthz(server_url: str):
    response = httpx.get(f"{server_url}/healthz")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert "X-Trace-ID" in response.headers


def test_e2e_ready(server_url: str):
    response = httpx.get(f"{server_url}/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_e2e_metrics(server_url: str):
    response = httpx.get(f"{server_url}/metrics")
    assert response.status_code == 200
    assert "http_request_duration_seconds" in response.text


def test_e2e_public_endpoints(server_url: str):
    for path in ["/api/status", "/api/faqs", "/api/timeline", "/api/sources"]:
        response = httpx.get(f"{server_url}{path}")
        assert response.status_code == 200, f"{path} failed: {response.text}"
        assert isinstance(response.json(), list)


def test_e2e_search(server_url: str):
    response = httpx.get(f"{server_url}/api/search", params={"q": "router"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

- [x] **Step 2: Run the E2E tests locally**

Run: `.venv/Scripts/pytest tests/test_e2e.py -v`
Expected: all tests pass; a uvicorn process starts and stops cleanly.

---

### Task 2: Backup/restore integration test

**Files:**
- Create: `tests/test_integration_workflow.py`

- [x] **Step 1: Create the integration test module**

Create `tests/test_integration_workflow.py`:

```python
"""Integration test for the database backup, restore, and validate workflow."""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from scripts.backup_db import backup_db
from scripts.restore_db import restore_db
from scripts.validate_db import validate_db


def test_backup_restore_validate_round_trip():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        try:
            conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY);")
            conn.execute("INSERT INTO t (id) VALUES (42);")
            conn.commit()
        finally:
            conn.close()

        backups_dir = tmp_path / "backups"
        backup_file = backup_db(db_path, backups_dir)
        assert backup_file.exists()

        restored_path = tmp_path / "restored.db"
        restore_db(backup_file, restored_path)

        result = validate_db(restored_path)
        assert result["integrity_check"] == "ok"

        conn = sqlite3.connect(str(restored_path))
        try:
            cursor = conn.execute("SELECT id FROM t")
            assert cursor.fetchone()[0] == 42
        finally:
            conn.close()
```

- [x] **Step 2: Run the integration test locally**

Run: `.venv/Scripts/pytest tests/test_integration_workflow.py -v`
Expected: the backup/restore/validate round trip passes.

---

### Task 3: Local dependency-audit target

**Files:**
- Modify: `Makefile`

- [x] **Step 1: Add an `audit` target**

Modify `Makefile` `.PHONY` line and add the target:

```makefile
.PHONY: help install lint format format-check type-check test validate build clean pre-commit api audit e2e
```

Add near the other targets:

```makefile
audit: ## Run pip-audit dependency security scan
	$(BIN)/pip-audit --desc

e2e: ## Run end-to-end tests against a real uvicorn server
	$(BIN)/pytest tests/test_e2e.py -v
```

- [x] **Step 2: Run the audit target**

Run: `make audit`
Expected: pip-audit completes; either no vulnerabilities are reported or known issues are documented.

---

### Task 4: Wire E2E and audit into CI

**Files:**
- Modify: `.github/workflows/ci.yml`

- [x] **Step 1: Add an E2E job**

Add after the `test` job:

```yaml
  e2e:
    runs-on: ubuntu-latest
    needs: [lint, type-check, test]
    steps:
      - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0
      - uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
      - name: Run end-to-end tests
        run: pytest tests/test_e2e.py -v
```

- [x] **Step 2: Update the dependency-audit job to use the Makefile target**

Change the last step of the existing `dependency-audit` job from:

```yaml
      - name: Audit dependencies
        run: pip-audit --desc
```

to:

```yaml
      - name: Audit dependencies
        run: make audit
```

- [x] **Step 3: Validate the workflow file syntax**

Run: `make pre-commit`
Expected: the YAML checks pass.

---

### Task 5: Verification

**Files:**
- None

- [x] **Step 1: Run linting, type checking, and the full test suite**

```bash
.venv/Scripts/ruff check .
.venv/Scripts/mypy app scripts tests
.venv/Scripts/pytest --cov-fail-under=60
```

Expected:
- `ruff check .` exits 0.
- `mypy app scripts tests` exits 0.
- `pytest` exits 0 with all tests passing and coverage >= 60%.

- [x] **Step 2: Run the new Makefile targets**

```bash
make audit
make e2e
make validate
make build
make pre-commit
```

Expected: all complete successfully.

---

## Self-Review

- **Spec coverage:** E2E tests (Task 1), integration workflow test (Task 2), local dependency scanning (Task 3), CI wiring (Task 4), and verification (Task 5) are all covered.
- **Placeholder scan:** No TBD/TODO placeholders; every step contains exact code or exact commands.
- **Type consistency:** `server_url` is a string, `_find_free_port` returns an int, and `backup_file` / `restored_path` are `Path` objects throughout.

---

## Final State

All tasks in this plan were implemented and verified.

### Completed deliverables

- `tests/test_e2e.py` — end-to-end tests that start a real uvicorn server and exercise `/healthz`, `/ready`, `/metrics`, public API endpoints, and `/api/search`.
- `tests/test_integration_workflow.py` — backup/restore/validate round-trip integration test.
- `Makefile` — added `audit` and `e2e` targets.
- `.github/workflows/ci.yml` — added `e2e` job and aligned `dependency-audit` to use `make audit`.
- `pyproject.toml` — added `setuptools>=78.1.1` to dev dependencies to keep the audit environment clean.

### Verified gates

- `ruff check .` ✅
- `mypy app scripts tests` ✅ (24 files)
- `pytest --cov-fail-under=60` ✅ 65 passed, ~85% coverage
- `make audit` ✅ no known vulnerabilities
- `make e2e` ✅ 5 passed
- `make validate` ✅
- `make build` ✅
- `make pre-commit` ✅

### Notes

- `pip-audit` skips the local editable package `fcc-router-consumer-awareness`; this is expected because it is not published on PyPI.
- The E2E tests spawn a subprocess uvicorn server and clean it up after each module; they add a few seconds to the total test runtime.
