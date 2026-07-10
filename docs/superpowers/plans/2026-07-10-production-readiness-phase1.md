# Production-Readiness Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish repository foundations so a new engineer can clone, install, lint, type-check, test, validate the database, and build the site with documented commands.

**Architecture:** Keep the existing stdlib SQLite API and static-site generator unchanged. Add a `pyproject.toml` based Python project, a `Makefile` for common commands, pre-commit hooks, an expanded GitHub Actions CI matrix, and project governance docs. This phase produces no new runtime behavior but makes the repository reproducible, testable, and contributor-friendly.

**Tech Stack:** Python 3.10+, ruff, mypy, pytest, coverage, pre-commit, pip-audit, GitHub Actions.

---

## File structure

| File | Responsibility |
|---|---|
| `pyproject.toml` | Project metadata, dev dependencies, and tool configuration (ruff, mypy, pytest, coverage) |
| `Makefile` | One-command targets for install, lint, type-check, test, validate, build |
| `.pre-commit-config.yaml` | Pre-commit hooks for ruff, mypy, trailing whitespace, etc. |
| `.github/workflows/ci.yml` | Lint, type-check, test, validate-db, build-site, dependency-audit jobs |
| `LICENSE` | Project license (CC0-1.0) |
| `CONTRIBUTING.md` | Contributor guidelines and local setup |
| `CODEOWNERS` | Default reviewers/owners |
| `SECURITY.md` | Security policy and reporting |
| `CHANGELOG.md` | Keep-a-Changelog skeleton |
| `tests/test_validate_db.py` | New pytest tests for the DB validation script |
| `README.md` | Updated quick-start and command reference |

---

## Task 1: Add `pyproject.toml`

**Files:**
- Create: `pyproject.toml`

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling>=1.24.0"]
build-backend = "hatchling.build"

[project]
name = "fcc-router-consumer-awareness"
version = "0.1.0"
description = "SQLite-backed data package and consumer-awareness website for FCC router Covered List actions."
readme = "README.md"
license = { text = "CC0-1.0" }
requires-python = ">=3.10"
authors = [
    { name = "FCC Router Consumer Awareness Contributors" },
]
keywords = ["fcc", "router", "consumer-awareness", "sqlite", "static-site"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

dependencies = []

[project.optional-dependencies]
dev = [
    "ruff>=0.5.0,<1",
    "mypy>=1.10.0,<3",
    "pytest>=8.2.0,<10",
    "pytest-cov>=5.0.0,<7",
    "pre-commit>=3.7.0,<5",
    "pip-audit>=2.7.0,<3",
]

[project.urls]
Homepage = "https://github.com/bmsull560/fcc-router-consumer-awareness"
Repository = "https://github.com/bmsull560/fcc-router-consumer-awareness"
Issues = "https://github.com/bmsull560/fcc-router-consumer-awareness/issues"

[tool.hatch.build.targets.wheel]
packages = ["app", "scripts"]

# ``app/`` and ``scripts/`` contain only stdlib Python, so runtime dependencies are empty.
# They still need ``__init__.py`` files to be valid hatchling packages.

[tool.ruff]
target-version = "py310"
line-length = 100
exclude = [
    ".git",
    ".github",
    "__pycache__",
    ".venv",
    "venv",
    "site",
    "site-data",
]

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "F",   # Pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "W",   # pycodestyle warnings
    "UP",  # pyupgrade
]
ignore = [
    "E501",  # line length handled by formatter
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "lf"

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
ignore_missing_imports = true
exclude = [
    "\\.git",
    "__pycache__",
    "\\.venv",
    "venv",
    "site",
    "site-data",
]

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = [
    "--strict-markers",
    "--cov=app",
    "--cov=scripts",
    "--cov-report=term-missing",
    "--cov-report=xml",
    "--cov-fail-under=60",
]

[tool.coverage.run]
source = ["app", "scripts"]
omit = [
    "site/*",
    "site-data/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

- [ ] **Step 2: Install the package in editable mode**

Run:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -e ".[dev]"
```

Expected: `pip` installs the package and dev tools without errors.

- [ ] **Step 3: Add package `__init__.py` files**

Create empty package markers so hatchling can build the declared packages.

Create `app/__init__.py`:

```python
"""Application package for FCC router consumer awareness."""
```

Create `scripts/__init__.py`:

```python
"""Build and maintenance scripts package."""
```

- [ ] **Step 4: Verify imports**

Run:

```bash
python -c "from app import sqlite_api; from scripts import build_site"
```

Expected: imports succeed without error.

---

## Task 2: Add `Makefile`

**Files:**
- Create: `Makefile`

- [ ] **Step 1: Write `Makefile`**

```makefile
.PHONY: help install lint format format-check type-check test validate build clean pre-commit

PYTHON := python
VENV := .venv
ifeq ($(OS),Windows_NT)
    BIN := $(VENV)/Scripts
else
    BIN := $(VENV)/bin
endif

help: ## Show this help message
	@$(PYTHON) -c "import re; \
	[print(f'  \\033[36m{m[0]:\u003c15}\\033[0m {m[1]}') for m in re.findall(r'^([a-zA-Z_-]+):.*?## (.*)$$', open('Makefile').read(), re.M)]"

install: ## Create venv and install project + dev dependencies
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -e ".[dev]"

lint: ## Run ruff linting
	$(BIN)/ruff check .

format: ## Auto-format with ruff
	$(BIN)/ruff format .

format-check: ## Check formatting without modifying files
	$(BIN)/ruff format --check .

type-check: ## Run mypy
	$(BIN)/mypy app scripts tests

test: ## Run pytest with coverage
	$(BIN)/pytest

validate: ## Validate the SQLite database
	$(BIN)/python scripts/validate_db.py

build: ## Build the static website
	$(BIN)/python scripts/build_site.py

pre-commit: ## Run pre-commit hooks on all files
	$(BIN)/pre-commit run --all-files

clean: ## Remove generated files and virtual environment
	$(BIN)/python -c "import shutil, os; \
	[shutil.rmtree(p, ignore_errors=True) for p in ['.venv','site-data','site/faqs','site/timeline','site/waivers','site/approvals','site/myths','site/sources','site/search']]; \
	[os.remove(f) for f in ['site/index.html'] if os.path.exists(f)]; \
	[shutil.rmtree(p, ignore_errors=True) for p in ['.pytest_cache','.mypy_cache','.ruff_cache']]; \
	[os.remove(f) for f in ['.coverage','coverage.xml'] if os.path.exists(f)]"
```

- [ ] **Step 2: Verify the Makefile targets work**

Run:

```bash
make help
make validate
make build
make test
```

Expected:
- `make help` prints target descriptions.
- `make validate` passes.
- `make build` passes.
- `make test` passes (20 tests, coverage ≥ 60%).

> Windows users without `make` can run the equivalent commands from the `Makefile` directly in Git Bash, or install `make` via `choco install make`.

---

## Task 3: Configure pre-commit

**Files:**
- Create: `.pre-commit-config.yaml`

- [ ] **Step 1: Write `.pre-commit-config.yaml`**

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-toml
      - id: check-added-large-files
        args: ["--maxkb=10240"]
      - id: check-merge-conflict

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.0
    hooks:
      - id: ruff
        args: ["--fix"]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
```

- [ ] **Step 2: Install the hooks**

Run:

```bash
source .venv/bin/activate
pre-commit install
```

Expected: `.git/hooks/pre-commit` is created.

---

## Task 4: Add project governance docs

**Files:**
- Create: `LICENSE`
- Create: `CONTRIBUTING.md`
- Create: `CODEOWNERS`
- Create: `SECURITY.md`
- Create: `CHANGELOG.md`

- [ ] **Step 1: Write `LICENSE` (CC0-1.0)**

```text
Creative Commons Legal Code

CC0 1.0 Universal

    CREATIVE COMMONS CORPORATION IS NOT A LAW FIRM AND DOES NOT PROVIDE
    LEGAL SERVICES. DISTRIBUTION OF THIS DOCUMENT DOES NOT CREATE AN
    ATTORNEY-CLIENT RELATIONSHIP. CREATIVE COMMONS PROVIDES THIS
    INFORMATION ON AN "AS-IS" BASIS. CREATIVE COMMONS MAKES NO WARRANTIES
    REGARDING THE USE OF THIS DOCUMENT OR THE INFORMATION OR WORKS
    PROVIDED HEREUNDER, AND DISCLAIMS LIABILITY FOR DAMAGES RESULTING FROM
    THE USE OF THIS DOCUMENT OR THE INFORMATION OR WORKS PROVIDED
    HEREUNDER.

Statement of Purpose

The laws of most jurisdictions throughout the world automatically confer
exclusive Copyright and Related Rights (defined below) upon the creator
and subsequent owner(s) (each and all, an "owner") of an original work of
authorship and/or a database (each, a "Work").

Certain owners wish to permanently relinquish those rights to a Work for
the purpose of contributing to a commons of creative, cultural and
scientific works ("Commons") that the public can reliably and without fear
of later claims of infringement build upon, modify, incorporate in other
works, reuse and redistribute as freely as possible in any form whatsoever
and for any purposes, including without limitation commercial purposes.
These owners may contribute to the Commons to promote the ideal of a free
culture and the further production of creative, cultural and scientific
works, or to gain reputation or greater distribution for their Work in
part through the use and efforts of others.

For these and/or other purposes and motivations, and without any
expectation of additional consideration or compensation, the person
associating CC0 with a Work (the "Affirmer"), to the extent that he or she
is an owner of Copyright and Related Rights in the Work, voluntarily
elects to apply CC0 to the Work and publicly distribute the Work under its
terms, with knowledge of his or her Copyright and Related Rights in the
Work and the meaning and intended legal effect of CC0 on those rights.

1. Copyright and Related Rights. A Work made available under CC0 may be
protected by copyright and related or neighboring rights ("Copyright and
Related Rights"). Copyright and Related Rights include, but are not
limited to, the following:

  i. the right to reproduce, adapt, distribute, perform, display,
     communicate, and translate a Work;
 ii. moral rights retained by the original author(s) and/or performer(s);
iii. publicity and privacy rights pertaining to a person's image or
     likeness depicted in a Work;
 iv. rights protecting against unfair competition in regards to a Work,
     subject to the limitations in paragraph 4(a), below;
  v. rights protecting the extraction, dissemination, use and reuse of data
     in a Work;
 vi. database rights (such as those arising under Directive 96/9/EC of the
     European Parliament and of the Council of 11 March 1996 on the legal
     protection of databases, and under any national implementation
     thereof, including any amended or successor version of such
     directive); and
vii. other similar, equivalent or corresponding rights throughout the
     world based on applicable law or treaty, and any national
     implementations thereof.

2. Waiver. To the greatest extent permitted by, but not in contravention
of, applicable law, Affirmer hereby overtly, fully, permanently,
irrevocably and unconditionally waives, abandons, and surrenders all of
Affirmer's Copyright and Related Rights and associated claims and causes
of action, whether now known or unknown (including existing as well as
future claims and causes of action), in the Work (i) in all territories
worldwide, (ii) for the maximum duration provided by applicable law or
treaty (including future time extensions), (iii) in any current or future
medium and for any number of copies, and (iv) for any purpose whatsoever,
including without limitation commercial, advertising or promotional
purposes (the "Waiver"). Affirmer makes the Waiver for the benefit of each
member of the public at large and to the detriment of Affirmer's heirs and
successors, fully intending that such Waiver shall not be subject to
revocation, rescission, cancellation, termination, or any other legal or
equitable action to disrupt the quiet enjoyment of the Work by the public
as contemplated by Affirmer's express Statement of Purpose.

3. Public License Fallback. Should any part of the Waiver for any reason
be judged legally invalid or ineffective under applicable law, then the
Waiver shall be preserved to the maximum extent permitted taking into
account Affirmer's express Statement of Purpose. In addition, to the
extent the Waiver is so judged Affirmer hereby grants to each affected
person a royalty-free, non transferable, non sublicensable, non exclusive,
irrevocable and unconditional license to exercise Affirmer's Copyright and
Related Rights in the Work (i) in all territories worldwide, (ii) for the
maximum duration provided by applicable law or treaty (including future
time extensions), (iii) in any current or future medium and for any number
of copies, and (iv) for any purpose whatsoever, including without
limitation commercial, advertising or promotional purposes (the
"License"). The License shall be deemed effective as of the date CC0 was
applied by Affirmer to the Work. Should any part of the License for any
reason be judged legally invalid or ineffective under applicable law, such
partial invalidity or ineffectiveness shall not invalidate the remainder
of the License, and in such case Affirmer hereby affirms that he or she
will not (i) exercise any of his or her remaining Copyright and Related
Rights in the Work or (ii) assert any associated claims and causes of
action with respect to the Work, in either case contrary to Affirmer's
express Statement of Purpose.

4. Limitations and Disclaimers.

 a. No trademark or patent rights held by Affirmer are waived, abandoned,
    surrendered, licensed or otherwise affected by this document.
 b. Affirmer offers the Work as-is and makes no representations or
    warranties of any kind concerning the Work, express, implied,
    statutory or otherwise, including without limitation warranties of
    title, merchantability, fitness for a particular purpose, non
    infringement, or the absence of latent or other defects, accuracy, or
    the present or absence of errors, whether or not discoverable, all to
    the greatest extent permissible under applicable law.
 c. Affirmer disclaims responsibility for clearing rights of other persons
    that may apply to the Work or any use thereof, including without
    limitation any person's Copyright and Related Rights in the Work.
    Further, Affirmer disclaims responsibility for obtaining any necessary
    consents, permissions or other rights required for any use of the
    Work.
 d. Affirmer understands and acknowledges that Creative Commons is not a
    party to this document and has no duty or obligation with respect to
    this CC0 or use of the Work.
```

- [ ] **Step 2: Write `CONTRIBUTING.md`**

```markdown
# Contributing

Thanks for your interest in helping improve the FCC Router Consumer Awareness project.

## Local setup

The project requires Python 3.10 or newer. The fastest way to set up a local environment is:

```bash
make install
```

If you prefer to set up the virtual environment manually, run the equivalent of:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install --upgrade pip
pip install -e ".[dev]"
```

This installs the package plus development tools (ruff, mypy, pytest, pytest-cov, pre-commit, pip-audit).

## Development commands

Run all common tasks through `make`:

| Task | Command |
|---|---|
| Lint | `make lint` |
| Format | `make format` |
| Type check | `make type-check` |
| Run tests | `make test` |
| Validate database | `make validate` |
| Build static site | `make build` |
| Run pre-commit hooks | `make pre-commit` |

## Pull request workflow

- Keep commits focused and easy to review.
- Add or update tests for any behavior change in `app/` or `scripts/`.
- CI must pass before merging.
- Update `CHANGELOG.md` under `## [Unreleased]`.

## Code style

- Python 3.10+.
- Type annotations are required for function signatures; mypy is enforced in CI.
- Linting and formatting are handled by ruff.
- Tests are written with pytest.

## Security reporting

Please see [`SECURITY.md`](SECURITY.md) for how to report vulnerabilities privately.

## License

By contributing, you agree that your contributions will be released under the CC0-1.0 license.
```

- [ ] **Step 3: Write `CODEOWNERS`**

```text
# Default reviewers for the whole repository
* @bmsull560
```

- [ ] **Step 4: Write `SECURITY.md`**

```markdown
# Security Policy

## Supported versions

Only the latest release on the `main` branch is supported with security updates.

## Reporting a vulnerability

Please report security issues privately via GitHub Security Advisories or by emailing the repository owner. Do not open a public issue for security bugs.

## Security practices

- No credentials are committed to source control.
- Configuration is environment-driven.
- Dependencies are scanned in CI with `pip-audit`.
```

- [ ] **Step 5: Write `CHANGELOG.md`**

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Phase 1 production-readiness foundations: governance docs (`CONTRIBUTING.md`, `CODEOWNERS`, `SECURITY.md`, `CHANGELOG.md`), `Makefile`-based workflow, and project metadata in `pyproject.toml`.
- Initial SQLite-backed data package for FCC router consumer awareness.
- `app/sqlite_api.py` stdlib-only JSON API with health, status, timeline, FAQs, alerts, sources, and search endpoints.
- `scripts/validate_db.py`, `scripts/export_site_json.py`, `scripts/build_site.py`, and `scripts/build_html.py` for validation, export, and static-site generation.
- `tests/` covering HTML rendering, JSON export determinism, and full site builds.
- `docs/database_README.md`, `docs/source-caveats.md`, and planning docs under `docs/superpowers/`.
- `LICENSE` (CC0-1.0).
```

---

## Task 5: Expand CI workflow

**Files:**
- Delete: `.github/workflows/validate-db.yml`
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Remove the old workflow file**

Run:

```bash
git rm .github/workflows/validate-db.yml
```

- [ ] **Step 2: Write `.github/workflows/ci.yml`**

```yaml
name: CI

on:
  push:
    branches: [main]
    tags: ["v*.*.*"]
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0
      - uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
      - name: Lint
        run: ruff check .
      - name: Check formatting
        run: ruff format --check .

  type-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0
      - uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
      - name: Type check
        run: mypy app scripts tests

  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0
      - uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
      - name: Run tests
        run: pytest

  validate-and-build:
    runs-on: ubuntu-latest
    needs: [lint, type-check, test]
    permissions:
      actions: write
      contents: read
    steps:
      - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0
      - uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1
        with:
          python-version: "3.12"
      - name: Validate database
        run: python scripts/validate_db.py
      - name: Build static site
        run: python scripts/build_site.py
      - name: Upload site artifact
        uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a
        with:
          name: site
          path: site/
          if-no-files-found: error

  dependency-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0
      - uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
      - name: Audit dependencies
        run: pip-audit --desc
```

- [ ] **Step 3: Verify workflow syntax**

Run:

```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"
```

Expected: exits 0.

---

## Task 6: Add tests for `validate_db.py`

**Files:**
- Create: `tests/test_validate_db.py`
- Modify: `scripts/validate_db.py` (refactor `main` into testable functions)

- [ ] **Step 1: Refactor `scripts/validate_db.py`**

Replace the script with the following version that keeps the same CLI behavior but exposes `validate(db_path: Path) -> dict[str, object]`:

```python
#!/usr/bin/env python3
"""Validate the FCC Router Consumer Awareness SQLite database."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "fcc_router_consumer_awareness.db"

TABLES = [
    "sources",
    "regulatory_events",
    "covered_list_entries",
    "definitions",
    "conditional_approvals",
    "waivers",
    "consumer_faqs",
    "claims",
    "audience_segments",
    "checklist_items",
    "alerts",
    "content_pages",
    "api_examples",
    "update_jobs",
    "data_notes",
]

VIEWS = [
    "vw_current_consumer_status",
    "vw_router_timeline",
    "vw_active_conditional_approvals",
    "vw_expiring_soon_conditional_approvals",
    "vw_active_waivers",
    "vw_public_faqs",
    "vw_primary_sources",
]


_KNOWN_NAMES = frozenset(TABLES) | frozenset(VIEWS)


def _count(conn: sqlite3.Connection, name: str) -> int:
    """Return the row count for a known table or view."""
    if name not in _KNOWN_NAMES:
        raise ValueError(f"Unknown table or view: {name}")
    return int(conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0])


def _safe_count(conn: sqlite3.Connection, name: str) -> int:
    """Return the row count for ``name``, or 0 if it does not exist."""
    try:
        return _count(conn, name)
    except sqlite3.OperationalError:
        return 0


def validate(db_path: Path) -> dict[str, object]:
    """Return validation results for the database at ``db_path``."""
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        integrity = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
    except sqlite3.DatabaseError as exc:
        if conn is not None:
            conn.close()
        raise ValueError(f"Not a valid SQLite database: {db_path}") from exc
    else:
        try:
            table_counts = {name: _safe_count(conn, name) for name in TABLES}
            view_counts = {name: _safe_count(conn, name) for name in VIEWS}
            fts5 = bool(
                conn.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='search_index'"
                ).fetchone()
            )
            fts5_match_count: int | None = None
            if fts5:
                fts5_match_count = int(
                    conn.execute(
                        "SELECT COUNT(*) FROM search_index WHERE search_index MATCH 'router'"
                    ).fetchone()[0]
                )
        finally:
            conn.close()

    return {
        "database": str(db_path),
        "integrity_check": integrity,
        "table_counts": table_counts,
        "view_counts": view_counts,
        "fts5_search_index_present": fts5,
        "fts5_match_count": fts5_match_count,
    }


def main() -> int:
    result = validate(DB_PATH)
    print(json.dumps(result, indent=2))
    return 0 if result["integrity_check"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Write `tests/test_validate_db.py`**

```python
import json
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from scripts.validate_db import TABLES, VIEWS, _count, main, validate

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "fcc_router_consumer_awareness.db"


def test_validate_real_database():
    result = validate(DB_PATH)
    assert result["integrity_check"] == "ok"
    assert result["database"] == str(DB_PATH)
    for table in TABLES:
        assert table in result["table_counts"]
        assert result["table_counts"][table] >= 0
    for view in VIEWS:
        assert view in result["view_counts"]
        assert result["view_counts"][view] >= 0
    assert result["fts5_search_index_present"] is True


def test_validate_missing_database():
    with tempfile.TemporaryDirectory() as tmp:
        missing = Path(tmp) / "missing.db"
        with pytest.raises(FileNotFoundError):
            validate(missing)


def test_validate_empty_database():
    with tempfile.TemporaryDirectory() as tmp:
        empty_db = Path(tmp) / "empty.db"
        sqlite3.connect(empty_db).close()
        result = validate(empty_db)
        assert result["integrity_check"] == "ok"
        assert all(count == 0 for count in result["table_counts"].values())
        assert all(count == 0 for count in result["view_counts"].values())
        assert result["fts5_search_index_present"] is False
        assert result["fts5_match_count"] is None


def test_validate_corrupt_database():
    with tempfile.TemporaryDirectory() as tmp:
        corrupt = Path(tmp) / "corrupt.db"
        corrupt.write_text("this is not a sqlite database", encoding="utf-8")
        with pytest.raises(ValueError):
            validate(corrupt)


def test_cli_returns_zero_for_valid_database():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_db.py")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["integrity_check"] == "ok"


def test_cli_returns_non_zero_for_failed_integrity():
    from scripts import validate_db
    original_validate = validate_db.validate

    def bad_validate(_db_path: Path):
        return {
            "database": str(_db_path),
            "integrity_check": "not ok",
            "table_counts": {},
            "view_counts": {},
            "fts5_search_index_present": False,
        }

    validate_db.validate = bad_validate
    try:
        assert main() == 1
    finally:
        validate_db.validate = original_validate


def test_count_rejects_unknown_identifier():
    conn = sqlite3.connect(":memory:")
    with pytest.raises(ValueError):
        _count(conn, "sources; DROP TABLE sources--")


def test_validate_real_database_exposes_fts5_match_count():
    result = validate(DB_PATH)
    assert result["fts5_search_index_present"] is True
    assert isinstance(result["fts5_match_count"], int)
    assert result["fts5_match_count"] >= 0
```

- [ ] **Step 3: Run the new tests**

Run the isolated tests without coverage (the project-level coverage gate is too low when only one test file runs):

```bash
.venv/Scripts/pytest tests/test_validate_db.py -v --no-cov
```

Expected: 8 tests pass.

Then run the full suite to confirm coverage:

```bash
.venv/Scripts/pytest
```

Expected: all tests pass and coverage is at least 60%.

---

## Task 7: Update `README.md`

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add a development section after the existing quick-start**

Insert the following block before `## Website-ready views`:

```markdown
## Development setup

```bash
make install
```

This creates `.venv/` and installs the project plus linting, formatting, type-checking, and testing tools.

## Development commands

| Command | Purpose |
|---|---|
| `make lint` | Run `ruff` linting |
| `make format` | Auto-format with `ruff format` |
| `make type-check` | Run `mypy` |
| `make test` | Run the pytest suite with coverage |
| `make validate` | Validate the SQLite database |
| `make build` | Build the static website |
| `make pre-commit` | Run pre-commit hooks on all files |

## CI

GitHub Actions runs lint, format check, type check, tests across Python 3.10–3.12, database validation, static-site build, and dependency auditing on every push and pull request.
```

- [ ] **Step 2: Update the test command**

Replace:

```bash
python3 -m unittest discover tests -v
```

with:

```bash
make test
```

- [ ] **Step 3: Fix the License section and workflow filename**

Find the `## License` section and replace it with:

```markdown
## License

This project is released into the public domain under the [CC0 1.0 Universal](LICENSE) license.
```

Find the file list near the top of the README and change `.github/workflows/validate-db.yml` to `.github/workflows/ci.yml` (update the description to "CI lint, test, and validation workflow").

---

## Task 8: Run lint, type-check, tests, validate, and build

**Files:**
- Modify: any existing `.py` files that fail lint/type-check

- [ ] **Step 1: Auto-format and fix lint issues**

Run:

```bash
source .venv/bin/activate
ruff format .
ruff check . --fix
```

Expected: formatter reformats files. If any lint errors remain, address them manually.

- [ ] **Step 2: Run type checking**

Run:

```bash
mypy app scripts tests
```

Expected: `Success: no issues found in ... source files`. If issues remain, add precise type annotations or targeted `# type: ignore` comments with explanatory notes.

- [ ] **Step 3: Run the full test suite**

Run:

```bash
pytest
```

Expected: all tests pass and coverage is at least 60%.

- [ ] **Step 4: Validate and build**

Run:

```bash
make validate
make build
```

Expected: validation JSON is printed and `site/` contains all expected HTML pages and `search/search_index.json`.

- [ ] **Step 5: Run pre-commit on all files**

Run:

```bash
make pre-commit
```

Expected: all hooks pass.

---

## Task 9: Final review and commit

- [ ] **Step 1: Review the diff**

Run:

```bash
git status
git diff
```

Expected: no unexpected files; `site-data/` and generated `site/*.html` remain ignored.

- [ ] **Step 2: Stage and commit**

Run:

```bash
git add pyproject.toml Makefile .pre-commit-config.yaml .github/workflows/ci.yml \
       LICENSE CONTRIBUTING.md CODEOWNERS SECURITY.md CHANGELOG.md \
       README.md scripts/validate_db.py tests/test_validate_db.py
git commit -m "chore: production-readiness foundations

- Add pyproject.toml with dev dependencies and tool configs
- Add Makefile and pre-commit hooks
- Expand CI with lint, type-check, matrix tests, build artifact, pip-audit
- Add LICENSE, CONTRIBUTING, CODEOWNERS, SECURITY, CHANGELOG
- Refactor validate_db.py for testability and add tests
- Update README with development commands"
```

---

## Spec coverage check

| Spec requirement | Task that implements it |
|---|---|
| Reproducible local development environment | Task 1 (`pyproject.toml`), Task 2 (`Makefile`) |
| Automated formatting, linting, type checking | Task 1 (tool configs), Task 5 (CI), Task 8 |
| Unit / integration tests | Task 1 (pytest config), Task 6 (validate_db tests), Task 8 |
| CI/CD pipeline | Task 5 (`.github/workflows/ci.yml`) |
| Dependency scanning | Task 5 (`dependency-audit` job) |
| Secure defaults / no credentials | Task 4 (`SECURITY.md`), env-driven config in design |
| Clear documentation / contribution guidelines | Task 4 (`CONTRIBUTING.md`), Task 7 (`README.md`) |
| Ownership | Task 4 (`CODEOWNERS`) |
| Semantic versioning / changelog | Task 4 (`CHANGELOG.md`), `pyproject.toml` version |

## Placeholder scan

- No `TBD`, `TODO`, or `implement later` strings.
- Every created file has complete content.
- Every command has an expected outcome.
- Type and function names are consistent across tasks.

## Next phases (out of scope for this plan)

- Phase 2: FastAPI modernization (endpoints, Pydantic models, logging, metrics, rate limiting).
- Phase 3: Containerization, migrations, backup/restore scripts, release/rollback workflow, runbooks.
- Phase 4: SLOs, alert examples, tracing, load-test baseline.
