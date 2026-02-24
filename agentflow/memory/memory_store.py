"""In-memory key-value and conversation memory store for AgentFlow agents."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Dict, List, Optional


@dataclass
class MemoryEntry:
    """A single memory entry with metadata."""
    key: str
    value: Any
    timestamp: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)
    ttl: Optional[float] = None  # seconds before expiry; None = no expiry

    @property
    def is_expired(self) -> bool:
        if self.ttl is None:
            return False
        return (time.time() - self.timestamp) > self.ttl

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "timestamp": self.timestamp,
            "tags": self.tags,
            "ttl": self.ttl,
        }


class MemoryStore:
    """Thread-safe in-memory store for agent conversation history and key-value data."""

    def __init__(self, max_size: int = 1000) -> None:
        self._store: Dict[str, MemoryEntry] = {}
        self._conversation: List[Dict[str, str]] = []
        self._lock = Lock()
        self.max_size = max_size

    # --- Key-Value API ---

    def set(self, key: str, value: Any, tags: List[str] = None, ttl: Optional[float] = None) -> None:
        """Store a key-value pair."""
        with self._lock:
            if len(self._store) >= self.max_size:
                self._evict_oldest()
            self._store[key] = MemoryEntry(key=key, value=value, tags=tags or [], ttl=ttl)

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value by key."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return default
            if entry.is_expired:
                del self._store[key]
                return default
            return entry.value

    def delete(self, key: str) -> bool:
        """Delete a key. Returns True if it existed."""
        with self._lock:
            return self._store.pop(key, None) is not None

    def search_by_tags(self, tags: List[str]) -> List[MemoryEntry]:
        """Find all entries matching given tags."""
        with self._lock:
            return [
                e for e in self._store.values()
                if any(t in e.tags for t in tags) and not e.is_expired
            ]

    def clear(self) -> None:
        """Clear all stored entries."""
        with self._lock:
            self._store.clear()

    def keys(self) -> List[str]:
        with self._lock:
            return list(self._store.keys())

    def size(self) -> int:
        with self._lock:
            return len(self._store)

    # --- Conversation History API ---

    def add_message(self, role: str, content: str) -> None:
        """Append a chat message to conversation history."""
        with self._lock:
            self._conversation.append({"role": role, "content": content})

    def get_history(self, last_n: Optional[int] = None) -> List[Dict[str, str]]:
        """Get conversation history, optionally limited to last N messages."""
        with self._lock:
            if last_n:
                return list(self._conversation[-last_n:])
            return list(self._conversation)

    def clear_history(self) -> None:
        """Clear conversation history."""
        with self._lock:
            self._conversation.clear()

    # --- Internal ---

    def _evict_oldest(self) -> None:
        """Remove oldest entry when max_size is reached."""
        if not self._store:
            return
        oldest_key = min(self._store, key=lambda k: self._store[k].timestamp)
        del self._store[oldest_key]

    def __repr__(self) -> str:
        return f"MemoryStore(size={len(self._store)}, messages={len(self._conversation)})"
