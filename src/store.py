from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document

class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        # Lab intentionally uses only the in-memory store. Do not attempt to
        # import ChromaDB here: an optional dependency could make the code take
        # an uninitialized branch on machines where chromadb happens to exist.
        self._use_chroma = False
        self._collection = None
        self._store: list[dict[str, Any]] = []
        self._next_index = 0

    def _make_record(self, doc: Document) -> dict[str, Any]:
        # Copy metadata instead of reusing the caller's dict.
        metadata = dict(doc.metadata or {})
        # Keep the original document/file id even when doc.id is a chunk id
        # such as "file#0". delete_document depends on this key.
        metadata.setdefault("doc_id", doc.id)
        doc_id = metadata["doc_id"]
        record = {
            "id": doc.id,
            "doc_id": doc_id,
            "content": doc.content,
            "embedding": self._embedding_fn(doc.content),
            "metadata": metadata,
        }
        return record

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        query_embedding = self._embedding_fn(query)
        scored_records = []
        for record in records:
            score = _dot(query_embedding, record["embedding"])
            scored_records.append((score, record))
        scored_records.sort(key=lambda item: item[0], reverse=True)
        results = []
        for score, record in scored_records[:top_k]:
            results.append({
                "id": record["id"],
                "doc_id": record["doc_id"],
                "content": record["content"],
                "metadata": record["metadata"],
                "score": score,
            })
        return results

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.
        """
        for doc in docs:
            record = self._make_record(doc)
            record["index"] = self._next_index
            self._next_index += 1
            self._store.append(record)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.
        """
        if top_k <= 0:
            return []
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if top_k <= 0:
            return []
        records = self._store
        if metadata_filter:
            records = [
                record
                for record in records
                if all(record.get("metadata", {}).get(key) == value for key, value in metadata_filter.items())
            ]
        return self._search_records(query, records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        remaining = []
        removed = False
        for record in self._store:
            if record.get("doc_id") == doc_id:
                removed = True
            else:
                remaining.append(record)
        self._store = remaining
        return removed
