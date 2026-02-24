"""In-memory and persistent context store for agent workflows."""
import json
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional
from agentflow.observability.logger import get_logger

logger = get_logger(__name__)


class MemoryStore:
    """Thread-safe in-memory key-value store with optional TTL and history."""

    def __init__(self, ttl_seconds: Optional[int] = None):
        self._store: Dict[str, Any] = {}
        self._timestamps: Dict[str, float] = {}
        self._history: Dict[str, List[Any]] = defaultdict(list)
        self._ttl = ttl_seconds

    def set(self, key: str, value: Any) -> None:
        """Store a value with optional TTL."""
        self._store[key] = value
        self._timestamps[key] = time.time()
        self._history[key].append({"value": value, "timestamp": self._timestamps[key]})
        logger.debug("memory_set", key=key)

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value, respecting TTL if configured."""
        if key not in self._store:
            return default
        if self._ttl and (time.time() - self._timestamps[key]) > self._ttl:
            self.delete(key)
            return default
        return self._store[key]

    def delete(self, key: str) -> None:
        """Remove a key from the store."""
        self._store.pop(key, None)
        self._timestamps.pop(key, None)

    def get_history(self, key: str) -> List[Any]:
        """Return full history of updates for a key."""
        return self._history.get(key, [])

    def all_keys(self) -> List[str]:
        """Return all active keys."""
        return list(self._store.keys())

    def snapshot(self) -> Dict[str, Any]:
        """Return a JSON-serializable snapshot of the store."""
        return {k: v for k, v in self._store.items()}

    def clear(self) -> None:
        """Clear all entries."""
        self._store.clear()
        self._timestamps.clear()
        logger.info("memory_cleared")


# Singleton instance for shared workflow state
memory_store = MemoryStore()
