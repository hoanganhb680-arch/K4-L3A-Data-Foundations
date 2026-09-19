from __future__ import annotations

import math
import re

class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks

class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        # Keep sentence bodies and their trailing delimiters separately, then
        # rejoin chunk text below instead of relying on a single regex with groups.
        matches = list(re.finditer(r".+?(?:\.\s|!\s|\?\s|\.$|!$|\?$|$)", text.strip(), flags=re.DOTALL))
        sentences: list[str] = [match.group(0).strip() for match in matches if match.group(0).strip()]

        if not sentences:
            stripped = text.strip()
            return [stripped] if stripped else []

        chunks: list[str] = []
        for start in range(0, len(sentences), self.max_sentences_per_chunk):
            group = sentences[start : start + self.max_sentences_per_chunk]
            chunks.append(" ".join(group))
        return [chunk.strip() for chunk in chunks if chunk.strip()]

class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        text = current_text.strip()
        if len(text) <= self.chunk_size:
            return [text] if text else []

        if remaining_separators:
            separator = remaining_separators[0]
            if separator:
                parts = text.split(separator)
            else:
                parts = [text]

            if separator and len(parts) > 1:
                results: list[str] = []
                for part in parts:
                    results.extend(self._split(part, remaining_separators[1:]))
                return results

            # No useful split at this level; try the next separator.
            split_results = self._split(text, remaining_separators[1:])
            if split_results:
                return split_results

        # Final fallback: break into fixed-size character chunks.
        chunks: list[str] = []
        for start in range(0, len(text), self.chunk_size):
            pieces = text[start : start + self.chunk_size].rstrip(" ")
            chunks.append(pieces)
        return [chunk for chunk in chunks if chunk]

def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))

def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    magnitude_a = math.sqrt(sum(x * x for x in vec_a))
    magnitude_b = math.sqrt(sum(x * x for x in vec_b))
    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (magnitude_a * magnitude_b)

class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=50).chunk(text),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=2).chunk(text),
            "recursive": RecursiveChunker(chunk_size=chunk_size).chunk(text),
        }
        result = {}
        for name, chunks in strategies.items():
            avg_length = (sum(len(chunk) for chunk in chunks) / len(chunks)) if chunks else 0.0
            result[name] = {"count": len(chunks), "avg_length": avg_length, "chunks": chunks}
        return result
