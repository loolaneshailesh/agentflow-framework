"""Structured logging configuration for AgentFlow."""
from __future__ import annotations
import logging
import sys
import structlog


def configure_logging(log_level: str = "INFO", json_logs: bool = False) -> None:
    """Configure structlog with standard or JSON rendering."""
    
    log_level_int = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure standard Python logging first
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level_int,
    )

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if json_logs:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__):
    """Get a structlog logger instance."""
    return structlog.get_logger(name)
