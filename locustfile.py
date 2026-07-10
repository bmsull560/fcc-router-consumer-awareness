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
