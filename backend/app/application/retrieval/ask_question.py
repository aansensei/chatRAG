import json
import os
import re
import unicodedata
from typing import Generator

import httpx

from app.infrastructure.vector.supabase.repository import search_chunks, keyword_search_chunks
from app.shared.utils.embedders.text_embedder import embed_text

_KEYWORD_RE = re.compile(r'\b([A-Z]{2,}-\d{3,}|\d{7,}|MST|[A-Z]{3,}\d+)\b')

_VI_ABBR = {
    "thuế": "MST", "lãnh đạo": "CEO", "giám đốc": "CEO",
    "hợp đồng": "contract", "ngân sách": "budget",
}

_OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
_OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:4b")
_TOP_K = int(os.environ.get("RETRIEVAL_TOP_K", 6))
_MAX_CHUNK_CHARS = int(os.environ.get("MAX_CHUNK_CHARS", 600))

_VI_CHARS = re.compile(r"[àáâãèéêìíòóôõùúýăđơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỷỹ]", re.IGNORECASE)

_SYSTEM_EN = (
    "You are a helpful assistant. Answer the user's question using ONLY the provided context. "
    "If the context does not contain enough information, say so honestly. "
    "Respond in English. Be concise and clear."
)

_SYSTEM_VI = (
    "Bạn là trợ lý phân tích tài liệu doanh nghiệp. "
    "Hãy trả lời câu hỏi DỰA TRÊN nội dung ngữ cảnh bên dưới. "
    "Ngữ cảnh có thể chứa dữ liệu bảng dạng: 'Tên chỉ số  Giá trị cũ  Giá trị mới  % thay đổi' — "
    "hãy đọc và trích xuất số liệu từ đó. "
    "Chỉ nói không đủ thông tin khi ngữ cảnh THỰC SỰ không chứa dữ liệu liên quan. "
    "Trả lời bằng tiếng Việt. Ngắn gọn và rõ ràng."
)


def _detect_lang(text: str) -> str:
    return "vi" if _VI_CHARS.search(text) else "en"


def _strip_accents(text: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


def _stream_groq(prompt: str, model: str, api_key: str) -> Generator[str, None, None]:
    with httpx.stream(
        "POST",
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "messages": [{"role": "user", "content": prompt}], "stream": True, "max_tokens": 2048},
        timeout=httpx.Timeout(connect=15.0, read=60.0, write=10.0, pool=10.0),
    ) as resp:
        if resp.status_code != 200:
            resp.read()
            try:
                msg = resp.json().get("error", {}).get("message", resp.text)
            except Exception:
                msg = resp.text
            yield _sse({"type": "token", "token": f"Lỗi Groq ({resp.status_code}): {msg}"})
            return
        for line in resp.iter_lines():
            if not line or line == "data: [DONE]":
                continue
            if line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                    token = data["choices"][0]["delta"].get("content", "")
                    if token:
                        yield _sse({"type": "token", "token": token})
                except Exception:
                    pass


def stream_ask(question: str, collections: list[str] | None = None, hybrid: bool = False, model: str | None = None, api_key: str | None = None) -> Generator[str, None, None]:
    ollama_model = model or _OLLAMA_MODEL
    lang = _detect_lang(question)

    try:
        yield _sse({"type": "step", "step": "embedding"})
        vector = embed_text(question)

        yield _sse({"type": "step", "step": "searching"})
        try:
            chunks = search_chunks(vector, match_count=_TOP_K, threshold=0.1, collections=collections or None)

            stripped_question = _strip_accents(question)
            if stripped_question != question:
                vector_stripped = embed_text(stripped_question)
                chunks_stripped = search_chunks(vector_stripped, match_count=_TOP_K, threshold=0.1, collections=collections or None)

                seen_ids = {c.get("id") for c in chunks if c.get("id")}
                for c in chunks_stripped:
                    c_id = c.get("id")
                    if c_id and c_id not in seen_ids:
                        chunks.append(c)
                        seen_ids.add(c_id)
                    elif not c_id:
                        if not any(e.get("content") == c.get("content") for e in chunks):
                            chunks.append(c)

            # Keyword fallback: exact codes (AAN-011, MST, numbers) + long query words
            kw_tokens = _KEYWORD_RE.findall(question)
            # Add words >= 4 chars (skips common stop words naturally)
            kw_tokens += [w for w in re.findall(r'\w+', question) if len(w) >= 4]
            # Expand Vietnamese terms to their abbreviations
            q_lower = question.lower()
            for vi_term, abbr in _VI_ABBR.items():
                if vi_term in q_lower:
                    kw_tokens.append(abbr)
            kw_tokens = list(dict.fromkeys(kw_tokens))  # deduplicate, preserve order
            if kw_tokens:
                seen_ids = {c.get("id") for c in chunks if c.get("id")}
                for kw_chunk in keyword_search_chunks(kw_tokens[:6], collections=collections or None):
                    if kw_chunk.get("id") not in seen_ids:
                        chunks.append(kw_chunk)
                        seen_ids.add(kw_chunk.get("id"))

            # Semantic hits first, section-expanded chunks (similarity=0) after.
            # Hard cap at _TOP_K * 2 to keep context within LLM limits.
            chunks.sort(key=lambda x: x.get("similarity", 0.0), reverse=True)
            chunks = chunks[: _TOP_K * 2]
        except Exception:
            chunks = []

        if not chunks and not hybrid:
            msg = (
                "Không tìm thấy thông tin liên quan trong tài liệu."
                if lang == "vi"
                else "No relevant information found in the documents."
            )
            yield _sse({"type": "done", "answer": msg, "sources": []})
            return

        sources = []
        for i, c in enumerate(chunks):
            meta = c.get("metadata") or {}
            raw_src = meta.get("source", "") if isinstance(meta, dict) else ""
            filename = raw_src.split("\\")[-1].split("/")[-1] if raw_src else f"Source {i+1}"
            sources.append({
                "id": f"src-{i}",
                "content": c["content"][:200],
                "section": c.get("section_title"),
                "similarity": round(c["similarity"], 3),
                "filename": filename,
            })

        yield _sse({"type": "sources", "sources": sources})

        if chunks:
            parts = []
            for i, c in enumerate(chunks):
                section = c.get("section_title") or ""
                header = f"[{i+1}]" + (f" [{section}]" if section else "")
                parts.append(f"{header}\n{c['content'][:_MAX_CHUNK_CHARS]}")
            context = "\n\n".join(parts)
            system = _SYSTEM_VI if lang == "vi" else _SYSTEM_EN
            prompt = f"{system}\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"
        else:
            system = (
                "Bạn là trợ lý AI thông minh. Hãy trả lời câu hỏi bằng kiến thức của bạn. Ngắn gọn và rõ ràng."
                if lang == "vi"
                else "You are a helpful AI assistant. Answer the question using your general knowledge. Be concise and clear."
            )
            prompt = f"{system}\n\nQuestion: {question}\nAnswer:"

        yield _sse({"type": "step", "step": "generating"})

        if api_key and api_key.startswith("gsk_"):
            groq_model = model or "llama-3.3-70b-versatile"
            yield from _stream_groq(prompt, groq_model, api_key)
        else:
            with httpx.stream(
                "POST",
                f"{_OLLAMA_URL}/api/generate",
                json={"model": ollama_model, "prompt": prompt, "stream": True},
                timeout=httpx.Timeout(connect=30.0, read=300.0, write=15.0, pool=10.0),
            ) as response:
                for line in response.iter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    if "error" in data:
                        yield _sse({"type": "done", "answer": f"Lỗi model: {data['error']}", "sources": sources})
                        return
                    token = data.get("response", "")
                    if token:
                        yield _sse({"type": "token", "token": token})
                    if data.get("done"):
                        break

        yield _sse({"type": "done", "sources": sources})

    except httpx.ConnectError:
        yield _sse({"type": "token", "token": "Không kết nối được đến Ollama. Hãy khởi động lại Ollama hoặc dùng Groq API key trong phần cài đặt model."})
        yield _sse({"type": "done", "sources": []})
    except Exception as exc:
        yield _sse({"type": "token", "token": f"Lỗi xử lý: {exc}"})
        yield _sse({"type": "done", "sources": []})
