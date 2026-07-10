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


def test_e2e_healthz(server_url: str) -> None:
    response = httpx.get(f"{server_url}/healthz")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert "X-Trace-ID" in response.headers


def test_e2e_ready(server_url: str) -> None:
    response = httpx.get(f"{server_url}/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_e2e_metrics(server_url: str) -> None:
    response = httpx.get(f"{server_url}/metrics")
    assert response.status_code == 200
    assert "http_request_duration_seconds" in response.text


def test_e2e_public_endpoints(server_url: str) -> None:
    for path in ["/api/status", "/api/faqs", "/api/timeline", "/api/sources"]:
        response = httpx.get(f"{server_url}{path}")
        assert response.status_code == 200, f"{path} failed: {response.text}"
        assert isinstance(response.json(), list)


def test_e2e_search(server_url: str) -> None:
    response = httpx.get(f"{server_url}/api/search", params={"q": "router"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
