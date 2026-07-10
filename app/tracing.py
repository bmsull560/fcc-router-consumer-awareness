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

import structlog.contextvars
from fastapi import Request
from starlette.responses import Response

TRACE_ID_HEADER = "X-Trace-ID"


def generate_trace_id() -> str:
    """Return a 12-character hex trace ID."""
    return uuid.uuid4().hex[:12]


def get_trace_id(request: Request) -> str:
    """Return the existing trace ID from headers or generate a new one."""
    header_value = request.headers.get(TRACE_ID_HEADER)
    if isinstance(header_value, str):
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
