"""Vector memory store with semantic search for AgentFlow agents."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class VectorEntry:
    """A document entry with its embedding."""
    doc_id: str
    text: str
    embedding: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)


class VectorMemoryStore:
    """
    Simple vector store for semantic similarity search.
    Uses numpy for dot-product similarity (cosine similarity with normalized vecs).
    Supports pluggable embedding backends (sentence-transformers, OpenAI, etc.).
    """

    def __init__(
        self,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        top_k: int = 5,
    ) -> None:
        self.embedding_model = embedding_model
        self.top_k = top_k
        self._entries: List[VectorEntry] = []
        self._embedder = None

    def _load_embedder(self) -> None:
        """Lazily load the embedding model."""
        if self._embedder is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            self._embedder = SentenceTransformer(self.embedding_model)
            logger.info(f"Loaded embedding model: {self.embedding_model}")
        except ImportError:
            raise ImportError(
                "sentence-transformers is required for VectorMemoryStore. "
                "Install it with: pip install sentence-transformers"
            )

    def _embed(self, text: str) -> List[float]:
        """Generate an embedding vector for the given text."""
        self._load_embedder()
        return self._embedder.encode(text, normalize_embeddings=True).tolist()

    def add(self, doc_id: str, text: str, metadata: Dict[str, Any] = None) -> None:
        """Add a document to the vector store."""
        embedding = self._embed(text)
        self._entries.append(VectorEntry(
            doc_id=doc_id,
            text=text,
            embedding=embedding,
            metadata=metadata or {},
        ))
        logger.debug(f"VectorStore: added doc '{doc_id}'")

    def search(self, query: str, top_k: Optional[int] = None) -> List[Tuple[VectorEntry, float]]:
        """Search for the most similar documents to the query."""
        if not self._entries:
            return []

        k = top_k or self.top_k
        query_vec = self._embed(query)

        try:
            import numpy as np
            q = np.array(query_vec)
            scores = []
            for entry in self._entries:
                score = float(np.dot(q, np.array(entry.embedding)))
                scores.append((entry, score))
            scores.sort(key=lambda x: x[1], reverse=True)
            return scores[:k]
        except ImportError:
            # Fallback: pure Python dot product
            scores = []
            for entry in self._entries:
                score = sum(a * b for a, b in zip(query_vec, entry.embedding))
                scores.append((entry, score))
            scores.sort(key=lambda x: x[1], reverse=True)
            return scores[:k]

    def search_texts(self, query: str, top_k: Optional[int] = None) -> List[str]:
        """Return just the text of top matching documents."""
        return [entry.text for entry, _ in self.search(query, top_k)]

    def delete(self, doc_id: str) -> bool:
        """Remove a document by ID."""
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.doc_id != doc_id]
        return len(self._entries) < before

    def clear(self) -> None:
        """Remove all documents."""
        self._entries.clear()

    def __len__(self) -> int:
        return len(self._entries)

    def __repr__(self) -> str:
        return f"VectorMemoryStore(docs={len(self._entries)}, model={self.embedding_model!r})"
