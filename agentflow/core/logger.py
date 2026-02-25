# agentflow/core/logger.py
from __future__ import annotations

import logging
import sys
from typing import Optional


def configure_logging(level: str = "INFO", name: Optional[str] = None) -> logging.Logger:
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger_name = name or "agentflow"
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def get_logger(name: str = "agentflow") -> logging.Logger:
    return logging.getLogger(name)
