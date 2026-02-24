"""Structured logging utilities for AgentFlow."""

from __future__ import annotations

import logging
import sys
from typing import Optional

_LOGGERS: dict = {}

DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Get or create a named logger with consistent formatting."""
    if name in _LOGGERS:
        return _LOGGERS[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(DEFAULT_FORMAT, datefmt=DEFAULT_DATE_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False

    _LOGGERS[name] = logger
    return logger


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    fmt: str = DEFAULT_FORMAT,
) -> None:
    """Configure root logging for the AgentFlow application."""
    handlers = [logging.StreamHandler(sys.stdout)]

    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(fmt, datefmt=DEFAULT_DATE_FORMAT))
        handlers.append(file_handler)

    logging.basicConfig(
        level=level,
        format=fmt,
        datefmt=DEFAULT_DATE_FORMAT,
        handlers=handlers,
    )

    # Suppress noisy third-party loggers
    for noisy in ["httpx", "httpcore", "openai", "anthropic", "litellm"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)


def set_level(name: str, level: int) -> None:
    """Dynamically change the log level of a named logger."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)
