"""Structured logging and observability for AgentFlow Framework."""
import logging
import sys
import time
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional
import structlog


def configure_logging(log_level: str = "INFO", json_logs: bool = False) -> None:
    """Configure structlog with optional JSON output."""
    shared_processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if json_logs:
        shared_processors.append(structlog.processors.JSONRenderer())
    else:
        shared_processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=shared_processors,
        wrapper_class=structlog.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a bound logger for a given module."""
    return structlog.get_logger(name)


class TraceContext:
    """Carries a trace ID through an agent execution chain."""

    def __init__(self, trace_id: Optional[str] = None):
        self.trace_id = trace_id or str(uuid.uuid4())
        self.spans: list = []
        self._start = time.perf_counter()

    def start_span(self, name: str) -> Dict[str, Any]:
        span = {"name": name, "start": time.perf_counter(), "trace_id": self.trace_id}
        self.spans.append(span)
        return span

    def end_span(self, span: Dict[str, Any]) -> float:
        elapsed = time.perf_counter() - span["start"]
        span["elapsed_ms"] = round(elapsed * 1000, 2)
        return elapsed

    def total_elapsed_ms(self) -> float:
        return round((time.perf_counter() - self._start) * 1000, 2)

    def summary(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "total_elapsed_ms": self.total_elapsed_ms(),
            "spans": self.spans,
        }


@contextmanager
def traced_operation(
    logger: structlog.BoundLogger, operation: str, **kwargs
) -> Generator[TraceContext, None, None]:
    """Context manager that logs start/end of an operation with timing."""
    ctx = TraceContext()
    logger.info(f"{operation}_start", trace_id=ctx.trace_id, **kwargs)
    try:
        yield ctx
        logger.info(
            f"{operation}_end",
            trace_id=ctx.trace_id,
            elapsed_ms=ctx.total_elapsed_ms(),
            **kwargs,
        )
    except Exception as exc:
        logger.error(
            f"{operation}_error",
            trace_id=ctx.trace_id,
            error=str(exc),
            elapsed_ms=ctx.total_elapsed_ms(),
            **kwargs,
        )
        raise


# Initialize on import
configure_logging()
