import os

import httpx

from app.infrastructure.vector.supabase.repository import search_chunks
from app.shared.utils.embedders.text_embedder import embed_text

_OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
_OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:4b")
_TOP_K = int(os.environ.get("RETRIEVAL_TOP_K", 5))

_SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer the user's question using ONLY the context below. "
    "If the context does not contain enough information, say so honestly. "
    "Be concise and clear."
)


def ask(question: str) -> dict:
    vector = embed_text(question)
    chunks = search_chunks(vector, match_count=_TOP_K, threshold=0.2)

    if not chunks:
        return {"answer": "Không tìm thấy thông tin liên quan trong tài liệu.", "sources": []}

    context = "\n\n".join(
        f"[{i+1}] {c['content']}" for i, c in enumerate(chunks)
    )
    prompt = f"{_SYSTEM_PROMPT}\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"

    response = httpx.post(
        f"{_OLLAMA_URL}/api/generate",
        json={"model": _OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=120,
    )
    response.raise_for_status()

    answer = response.json()["response"].strip()
    sources = [
        {"content": c["content"][:200], "section": c.get("section_title"), "similarity": round(c["similarity"], 3)}
        for c in chunks
    ]
    return {"answer": answer, "sources": sources}
