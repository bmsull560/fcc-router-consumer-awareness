"""Integration tests for the FastAPI application."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api import app, limiter


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    limiter.reset()
    yield


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


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


def test_trace_id_header(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert "X-Trace-ID" in response.headers
    assert len(response.headers["X-Trace-ID"]) == 12


def test_trace_id_header_is_propagated(client):
    trace_id = "abc123def456"
    response = client.get("/healthz", headers={"X-Trace-ID": trace_id})
    assert response.headers["X-Trace-ID"] == trace_id


def test_metrics_endpoint(client):
    # Prime at least one request so default latency metrics are present.
    client.get("/healthz")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_request_duration_seconds" in response.text


def test_not_found(client):
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert "error" in response.json()
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "X-Trace-ID" in response.headers


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
