"""General-purpose helper utilities for AgentFlow."""

from __future__ import annotations

import asyncio
import json
import uuid
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar

T = TypeVar("T")


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID, optionally prefixed."""
    uid = str(uuid.uuid4()).replace("-", "")[:16]
    return f"{prefix}_{uid}" if prefix else uid


def truncate_text(text: str, max_chars: int = 500, suffix: str = "...") -> str:
    """Truncate text to a maximum character length."""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - len(suffix)] + suffix


def flatten_dict(d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """Flatten a nested dictionary with dot-separated keys."""
    items: List = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def safe_json_loads(text: str, default: Any = None) -> Any:
    """Safely parse JSON, returning default on failure."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: Any, indent: Optional[int] = None) -> str:
    """Serialize object to JSON string, handling non-serializable types gracefully."""
    def _default(o: Any) -> str:
        return repr(o)
    return json.dumps(obj, default=_default, indent=indent, ensure_ascii=False)


def chunk_list(lst: List[T], chunk_size: int) -> List[List[T]]:
    """Split a list into chunks of the given size."""
    return [lst[i: i + chunk_size] for i in range(0, len(lst), chunk_size)]


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge multiple dicts (later values override earlier ones)."""
    result: Dict[str, Any] = {}
    for d in dicts:
        for k, v in d.items():
            if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                result[k] = merge_dicts(result[k], v)
            else:
                result[k] = v
    return result


def retry_async(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """
    Async retry decorator with exponential backoff.

    Usage:
        @retry_async(max_retries=3, delay=1.0)
        async def my_func(): ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            last_exc: Optional[Exception] = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    if attempt < max_retries:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
            raise last_exc  # type: ignore
        return wrapper
    return decorator


def is_async_callable(obj: Any) -> bool:
    """Check if an object is an async callable."""
    return asyncio.iscoroutinefunction(obj) or (
        callable(obj) and asyncio.iscoroutinefunction(getattr(obj, "__call__", None))
    )
