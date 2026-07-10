FROM python:3.12-slim

WORKDIR /app

# Install build dependencies and the project.
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir -e "."

# Copy application code, scripts, and the initial database.
COPY app/ app/
COPY scripts/ scripts/
COPY migrations/ migrations/
COPY data/ data/

# Create a non-root user and ensure the app directory is writable.
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && chown -R appuser:appuser /app
USER appuser

ENV PYTHONUNBUFFERED=1
ENV FCC_DB_PATH=/app/data/fcc_router_consumer_awareness.db

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c 'import urllib.request; urllib.request.urlopen("http://localhost:8000/healthz").read()' || exit 1

# Run migrations on startup, then start the API.
CMD ["sh", "-c", "python scripts/migrate.py migrate && uvicorn app.api:app --host 0.0.0.0 --port 8000"]
