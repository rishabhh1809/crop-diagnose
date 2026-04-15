"""
app/logging.py
──────────────
Configures structlog for structured, JSON-ready logging.
In development the output is colourful and human-readable.
In production (LOG_LEVEL=INFO, no TTY) it emits JSON lines.

Call `configure_logging()` once at process start (inside main.py lifespan).
Then use `get_logger(__name__)` everywhere instead of stdlib logging.
"""

import logging
import sys

import structlog
from app.config import settings


def configure_logging() -> None:
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Wire stdlib logging through structlog so third-party libs (uvicorn,
    # onnxruntime) also emit structured records.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    is_tty = sys.stdout.isatty()

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if is_tty:
        # Human-readable coloured output for local dev.
        renderer: structlog.types.Processor = structlog.dev.ConsoleRenderer()
    else:
        # JSON lines for log aggregators (Loki, Datadog, CloudWatch, etc.).
        shared_processors.append(structlog.processors.format_exc_info)
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(log_level)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
