.PHONY: help install lint format format-check type-check test validate build clean pre-commit api audit e2e

PYTHON := python
VENV := .venv
ifeq ($(OS),Windows_NT)
    BIN := $(VENV)/Scripts
else
    BIN := $(VENV)/bin
endif

help: ## Show this help message
	@$(PYTHON) -c "import re; \
	[print(f'  \033[36m{m[0]:<15}\033[0m {m[1]}') for m in re.findall(r'^([a-zA-Z_-]+):.*?## (.*)$$', open('Makefile').read(), re.M)]"

install: ## Create venv and install project + dev dependencies
	$(PYTHON) -m venv $(VENV)
	$(BIN)/python -m pip install --upgrade pip
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
	$(BIN)/pytest --cov-fail-under=60

validate: ## Validate the SQLite database
	$(BIN)/python scripts/validate_db.py

backup: ## Create a timestamped, integrity-checked backup of the database
	$(BIN)/python scripts/backup_db.py

restore: ## Restore the database from a backup (pass BACKUP=path)
ifndef BACKUP
	$(error BACKUP is not set. Usage: make restore BACKUP=path/to/backup.db.gz)
endif
	$(BIN)/python scripts/restore_db.py $(BACKUP) --force

build: ## Build the static website
	$(BIN)/python scripts/build_site.py

pre-commit: ## Run pre-commit hooks on all files
	$(BIN)/pre-commit run --all-files

clean: ## Remove generated files and virtual environment
	$(PYTHON) -c "import shutil, os; \
	[shutil.rmtree(p, ignore_errors=True) for p in ['.venv','site-data','site/faqs','site/timeline','site/waivers','site/approvals','site/myths','site/sources','site/search']]; \
	[os.remove(f) for f in ['site/index.html'] if os.path.exists(f)]; \
	[shutil.rmtree(p, ignore_errors=True) for p in ['.pytest_cache','.mypy_cache','.ruff_cache']]; \
	[os.remove(f) for f in ['.coverage','coverage.xml'] if os.path.exists(f)]"

api: ## Run the FastAPI development server with auto-reload
	$(BIN)/uvicorn app.api:app --reload

audit: ## Run pip-audit dependency security scan
	$(BIN)/pip-audit --desc

e2e: ## Run end-to-end tests against a real uvicorn server
	$(BIN)/pytest tests/test_e2e.py -v
