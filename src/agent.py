from typing import Callable

from .store import EmbeddingStore

class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        if self.store.get_collection_size() == 0:
            return "Không tìm thấy tài liệu liên quan trong kho tri thức."

        results = self.store.search(question, top_k=top_k)
        if not results:
            return "Không tìm thấy ngữ cảnh phù hợp để trả lời câu hỏi."

        context_parts = []
        for index, item in enumerate(results, start=1):
            metadata = item.get("metadata", {})
            source = metadata.get("source_url") or metadata.get("doc_id") or item.get("doc_id") or "unknown"
            content = item.get("content", "")
            context_parts.append(
                f"[{index}] SOURCE: {source}\n{content}"
            )

        prompt = (
            "Answer the question using ONLY the context below. "
            "Cite the source number(s) that support your answer, for example [1] or [1][2]. "
            "If the context is insufficient, explicitly say that you cannot find the answer.\n\n"
            f"Question: {question}\n\n"
            f"Context:\n{chr(10).join(context_parts)}\n\n"
            "Answer:"
        )
        return self.llm_fn(prompt)