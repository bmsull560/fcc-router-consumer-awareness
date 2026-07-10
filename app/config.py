"""Application configuration via Pydantic Settings."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """Environment-driven settings.

    Variables are read with the ``FCC_`` prefix by default, e.g.
    ``FCC_DB_PATH``, ``FCC_CORS_ORIGINS``.
    """

    app_name: str = "FCC Router Consumer Awareness API"
    debug: bool = False
    db_path: Path = ROOT / "data" / "fcc_router_consumer_awareness.db"
    cors_origins: list[str] = []
    log_level: str = "INFO"

    model_config = {"env_prefix": "FCC_"}


def get_settings() -> Settings:
    """Return a cached-ish Settings instance."""
    return Settings()
