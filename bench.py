#!/usr/bin/env python3
"""Manual benchmark runner for K4-L3A Day 7 retrieval comparison.

This script is deliberately separate from `src/`: it reads the group corpus
from `data/dorms`, splits each document body with the chosen personal strategy,
and evaluates five benchmark queries against the in-memory vector store.

Only change the CHUNK_STRATEGY section when comparing individual strategies.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv

from src.chunking import FixedSizeChunker, SentenceChunker, RecursiveChunker
from src.embeddings import GeminiEmbedder, MockEmbedder, _mock_embed
from src.models import Document
from src.store import EmbeddingStore

CORPUS_DIR = Path("data/dorms")
OUTPUT_PATH = Path("ket_qua_benchmark.txt")

# ---------------------------------------------------------------------------
# PERSONAL STRATEGY:
# Mỗi người chỉ sửa ĐÚNG MỘT DÒNG dưới đây.
# Ba lựa chọn có sẵn:
#   CHUNKER = FixedSizeChunker(chunk_size=500, overlap=50)
#   CHUNKER = SentenceChunker(max_sentences_per_chunk=2)
#   CHUNKER = RecursiveChunker(chunk_size=500)
# ---------------------------------------------------------------------------
CHUNKER = SentenceChunker(max_sentences_per_chunk=2)

# In embedded text matching we ignore case and whitespace differences.
def _normalise(value: str) -> str:
    return re.sub(r"\s+", " ", value).lower()

BENCHMARKS = [
    {
        "id": "Q1",
        "query": "Tân sinh viên có thể đăng ký ở nội trú qua hình thức nào?",
        "gold_needle": "online",
        "gold_doc_ids": {"dorm-registration", "tmu-dormitory-registration-hanoi"},
        "metadata_filter": {"audience": "student"},
    },
    {
        "id": "Q2",
        "query": "Mức phí ở ký túc xá PTIT cơ sở miền Bắc được ban hành theo quyết định số mấy?",
        "gold_needle": "1521/qđ-hv",
        "gold_doc_ids": {"dorm-charge"},
        "metadata_filter": None,
    },
    {
        "id": "Q3",
        "query": "Ký túc xá Đại học Bách khoa Hà Nội có tổng cộng bao nhiêu phòng ở?",
        "gold_needle": "435 phòng",
        "gold_doc_ids": {"hust-dormitory-overview"},
        "metadata_filter": None,
    },
    {
        "id": "Q4",
        "query": "Văn bản điều chỉnh mức giá điện nước tại khu nội trú TMU được ban hành khi nào?",
        "gold_needle": "05/08/2024",
        "gold_doc_ids": {"tmu-dormitory-electric-water-fees"},
        "metadata_filter": None,
    },
    {
        "id": "Q5",
        "query": "Đối tượng nào được ưu tiên khi xét duyệt chỗ ở nội trú?",
        "gold_needle": "thương binh",
        "gold_doc_ids": {"dorm-registration", "tmu-dormitory-registration-hanoi", "dorm-slot"},
        "metadata_filter": None,
    },
]


@dataclass
class SourceDocument:
    path: Path
    metadata: dict[str, str]
    content: str


def parse_markdown(path: Path) -> SourceDocument:
    """Split YAML frontmatter metadata from the body."""
    text = path.read_text(encoding="utf-8")
    metadata: dict[str, str] = {}
    body = text.strip()

    match = re.search(r"^---\s*\n(.*?)\n---\s*$", text, flags=re.MULTILINE | re.DOTALL)
    if match:
        block = match.group(1)
        body = text[match.end() :].strip()
        for line in block.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip().rstrip("#").strip().strip('"')
            if key:
                metadata[key] = value

    metadata.setdefault("doc_id", path.stem)
    return SourceDocument(path=path, metadata=metadata, content=body)


def build_embedder() -> Callable[[str], list[float]]:
    """Choose a real backend when configured, otherwise a clearly-labelled mock."""
    load_dotenv(override=False)
    provider = os.getenv("EMBEDDING_PROVIDER", "").strip().lower()
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if provider in {"", "gemini"} and api_key:
        try:
            return GeminiEmbedder()
        except Exception as exc:
            print(f"[warn] Could not start GeminiEmbedder: {exc}", file=sys.stderr)
            print("[warn] Falling back to mock embeddings. Interpret scores accordingly.", file=sys.stderr)
    return _mock_embed


if __name__ == "__main__":
    import sys

    # Tự động gán tên strategy từ object chunker; không cần sửa dòng này.
    if isinstance(CHUNKER, FixedSizeChunker):
        STRATEGY_NAME = f"FixedSizeChunker(chunk_size={CHUNKER.chunk_size}, overlap={CHUNKER.overlap})"
    elif isinstance(CHUNKER, SentenceChunker):
        STRATEGY_NAME = f"SentenceChunker(max_sentences_per_chunk={CHUNKER.max_sentences_per_chunk})"
    elif isinstance(CHUNKER, RecursiveChunker):
        separators = CHUNKER.separators
        separators_label = ", ".join(repr(sep) for sep in separators) if separators else "[]"
        STRATEGY_NAME = f"RecursiveChunker(chunk_size={CHUNKER.chunk_size}, separators=[{separators_label}])"
    else:
        STRATEGY_NAME = f"{type(CHUNKER).__name__}(custom)"

    lines: list[str] = []
    print(f"Strategy: {STRATEGY_NAME}")
    print(f"Corpus dir: {CORPUS_DIR}")

    source_files = sorted(CORPUS_DIR.glob("*.md"))
    if len(source_files) < 5:
        print(f"[error] Found {len(source_files)} markdown files; expected 5-10.", file=sys.stderr)
        raise SystemExit(2)

    embedder = build_embedder()
    try:
        embedder("benchmark backend probe")
        print("Embedding backend:", getattr(embedder, "_backend_name", type(embedder).__name__))
    except Exception as exc:
        print(f"[warn] Embedding backend probe failed: {exc}", file=sys.stderr)
        print("[warn] Falling back to mock. Record scores are unreliable.", file=sys.stderr)
        embedder = _mock_embed
        print("Embedding backend:", getattr(embedder, "_backend_name", type(embedder).__name__))

    store = EmbeddingStore(collection_name="dorms", embedding_fn=embedder)
    loaded = 0
    for path in source_files:
        source_doc = parse_markdown(path)
        chunks = CHUNKER.chunk(source_doc.content)
        for index, chunk in enumerate(chunks):
            metadata = dict(source_doc.metadata)
            metadata["doc_id"] = source_doc.path.stem
            metadata["chunk_index"] = str(index)
            store.add_documents(
                [
                    Document(
                        id=f"{path.stem}#{index}",
                        content=chunk,
                        metadata=metadata,
                    )
                ]
            )
            loaded += 1

    print(f"Loaded {len(source_files)} files -> {loaded} chunks")
    print("=" * 100)
    lines.extend([f"Strategy: {STRATEGY_NAME}", f"Loaded {len(source_files)} files -> {loaded} chunks", "=" * 100])

    total_score = 0
    max_score = 0
    for case in BENCHMARKS:
        query = case["query"]
        needle = _normalise(case["gold_needle"])
        metadata_filter = case.get("metadata_filter")

        if metadata_filter:
            results = store.search_with_filter(query, top_k=3, metadata_filter=metadata_filter)
            # A/B diagnostic required by the lab: same query without the filter.
            unfiltered = store.search(query, top_k=3)
        else:
            results = store.search(query, top_k=3)
            unfiltered = None

        context = " ".join(_normalise(item.get("content", "")) for item in results)
        needle_found = needle in context
        top_doc_ids = [item.get("doc_id") or item.get("metadata", {}).get("doc_id") for item in results]
        gold_only = case["gold_doc_ids"]

        # Exact-content two-level scoring.
        relevant_positions = [i for i, doc_id in enumerate(top_doc_ids, start=1) if doc_id in gold_only]
        if needle_found and relevant_positions:
            score = 2 if relevant_positions[0] == 1 else 1
        elif not relevant_positions and needle_found:
            # Recall-oriented edge case: relevant content reached even if doc id was
            # outside the declared gold set. Keep it visible instead of hiding it.
            score = 1
        else:
            score = 0

        total_score += score
        max_score += 2

        print(f"\n{case['id']} | filter={metadata_filter or 'none'} | score={score}/2")
        print("Query:", query)
        if metadata_filter and unfiltered is not None:
            print("-- Unfiltered A/B top-3 --")
            for rank, item in enumerate(unfiltered, start=1):
                print(f"  [U{rank}] score={item.get('score', 0):.4f} doc={item.get('doc_id', '?')}")
                print(f"        {item.get('content', '')[:140].replace(chr(10), ' ')}")
            print("-- Filtered top-3 --")
        print("Gold needle found in context:", needle_found)
        print("Top doc ids:", top_doc_ids)
        print("Declared gold doc ids:", sorted(gold_only))

        for rank, item in enumerate(results, start=1):
            preview = item.get("content", "").replace("\n", " ")
            print(f"  [{rank}] score={item.get('score', 0):.4f} doc={item.get('doc_id', '?')}")
            print(f"      {preview[:160]}")

        lines.append(
            "\n".join(
                [
                    f"{case['id']} | filter={metadata_filter or 'none'} | score={score}/2",
                    f"Query: {query}",
                    f"Gold needle found in context: {needle_found}",
                    f"Top doc ids: {top_doc_ids}",
                    f"Declared gold doc ids: {sorted(gold_only)}",
                    f"Final score: {score}/2",
                    f"Overall total so far: {total_score}/{max_score}",
                ]
            )
        )

        lines.extend(
            f"  [{rank}] score={item.get('score', 0):.4f} doc={item.get('doc_id', '?')}"
            for rank, item in enumerate(results, start=1)
        )

    print("\n" + "=" * 100)
    print(f"Retrieval quality: {total_score}/{max_score}")
    lines.extend(["=" * 100, f"Retrieval quality: {total_score}/{max_score}"])
    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Saved: {OUTPUT_PATH}")