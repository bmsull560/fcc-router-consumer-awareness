"""Structured logging configuration using structlog."""

from __future__ import annotations

import logging.config
from typing import Any, cast

import structlog
from structlog.typing import Processor


def configure_logging(log_level: str, json_format: bool = True) -> None:
    """Configure structlog and stdlib logging.

    When ``json_format`` is True, logs are emitted as JSON. When False, logs are
    emitted in a human-readable console format suitable for local development.

    The ``merge_contextvars`` processor ensures that ``trace_id`` bound by the
    request tracing middleware is included in every log record.
    """
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.ExtraAdder(),
        structlog.processors.format_exc_info,
    ]

    formatter_processor: Processor = (
        structlog.processors.JSONRenderer()
        if json_format
        else structlog.dev.ConsoleRenderer(colors=True)
    )

    structlog.configure(
        processors=shared_processors + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": formatter_processor,
                    "foreign_pre_chain": shared_processors,
                },
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                },
            },
            "loggers": {
                "": {"handlers": ["default"], "level": log_level},
            },
        }
    )


def get_logger(*args: Any, **kwargs: Any) -> structlog.stdlib.BoundLogger:
    """Return a structlog logger."""
    return cast(structlog.stdlib.BoundLogger, structlog.get_logger(*args, **kwargs))
