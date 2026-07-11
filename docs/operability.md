# Operability Runbook

## Build pipeline

```bash
python3 scripts/validate_db.py
python3 scripts/build_site.py --out site --site-data site-data
```

## Local validation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
ruff format --check scripts app tests
ruff check scripts app tests
mypy scripts app tests
python3 -m pytest tests/ -v
```

## Run the JSON API

```bash
python3 -m app.sqlite_api --port 8000
```

Health check: `curl http://localhost:8000/healthz`

## Troubleshooting

- **Database not found**: verify `data/fcc_router_consumer_awareness.db` exists and is readable.
- **Build fails with `No module named 'scripts'`**: run from the repo root and ensure `PYTHONPATH` includes it.
- **Coverage fails**: run the full suite; direct invocation tests are required for subprocess-covered modules.
- **Mobile nav invisible**: check that `site/static/style.css` was copied; the responsive rules now show links on narrow screens.
