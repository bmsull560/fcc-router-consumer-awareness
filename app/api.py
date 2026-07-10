"""FastAPI application for the FCC router awareness dataset."""

from __future__ import annotations

import sqlite3
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_settings
from app.db import get_db_conn
from app.logging import configure_logging, get_logger
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
from app.tracing import tracing_middleware


def _rows_as_dicts(cursor: sqlite3.Cursor) -> list[dict[str, object]]:
    columns = [d[0] for d in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level, json_format=not settings.debug)
    if not settings.db_path.exists():
        raise RuntimeError(f"Database not found: {settings.db_path}")
    yield


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.middleware("http")
async def add_security_headers(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


app.middleware("http")(tracing_middleware)


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


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    if exc.status_code == 404:
        return _secure_json_response(request, 404, {"error": "Not found"})
    return _secure_json_response(request, exc.status_code, {"error": exc.detail})


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


Instrumentator().instrument(app).expose(app)


@app.get("/healthz", response_model=HealthResponse)
def healthz() -> dict[str, bool]:
    return {"ok": True}


@app.get("/ready", response_model=ReadyResponse)
def ready(db: sqlite3.Connection = Depends(get_db_conn)) -> dict[str, str]:
    try:
        db.execute("SELECT 1")
        return {"status": "ok"}
    except sqlite3.Error as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@app.get("/api/status", response_model=list[StatusResponse])
def get_status(db: sqlite3.Connection = Depends(get_db_conn)) -> list[dict[str, object]]:
    cursor = db.execute("SELECT * FROM vw_current_consumer_status")
    return _rows_as_dicts(cursor)


@app.get("/api/faqs", response_model=list[FAQResponse])
def get_faqs(db: sqlite3.Connection = Depends(get_db_conn)) -> list[dict[str, object]]:
    cursor = db.execute("SELECT * FROM vw_public_faqs ORDER BY category, question")
    return _rows_as_dicts(cursor)


@app.get("/api/timeline", response_model=list[TimelineResponse])
def get_timeline(db: sqlite3.Connection = Depends(get_db_conn)) -> list[dict[str, object]]:
    cursor = db.execute("SELECT * FROM vw_router_timeline ORDER BY event_date DESC")
    return _rows_as_dicts(cursor)


@app.get("/api/alerts", response_model=list[AlertResponse])
def get_alerts(db: sqlite3.Connection = Depends(get_db_conn)) -> list[dict[str, object]]:
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
def get_sources(db: sqlite3.Connection = Depends(get_db_conn)) -> list[dict[str, object]]:
    cursor = db.execute(
        "SELECT * FROM vw_primary_sources ORDER BY publication_date DESC, source_key DESC"
    )
    return _rows_as_dicts(cursor)


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
