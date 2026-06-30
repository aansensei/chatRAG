import os

import httpx
import os
import re
import httpx
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.application.retrieval.ask_question import stream_ask
from app.infrastructure.vector.supabase.repository import list_documents
from app.presentation.api.auth import get_collections

_OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
_OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:4b")

router = APIRouter(prefix="/chat", tags=["chat"])

_OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

_FALLBACK_SUGGESTIONS = [
    {"title": "Tóm tắt tài liệu", "subtitle": "Các điểm chính trong kho tài liệu"},
    {"title": "Thông tin công ty", "subtitle": "Ban lãnh đạo và cơ cấu tổ chức"},
    {"title": "Kết quả tài chính", "subtitle": "Doanh thu, lợi nhuận và chỉ số KPI"},
    {"title": "Kế hoạch nhân sự", "subtitle": "Tuyển dụng, đào tạo và phúc lợi"},
]


class HistoryMessage(BaseModel):
    role: str
    content: str


class QuestionRequest(BaseModel):
    question: str
    collections: list[str] | None = None
    collection: str = "default"
    hybrid: bool = False
    model: str | None = None
    api_key: str | None = None
    history: list[HistoryMessage] | None = None


@router.post("")
def chat(body: QuestionRequest, dep_collections: list[str] = Depends(get_collections)):
    if dep_collections:
        active = dep_collections
    elif body.collections is not None:
        active = body.collections or None
    elif body.collection != "default":
        active = [body.collection]
    else:
        active = None
    history = [h.model_dump() for h in body.history] if body.history else None
    return StreamingResponse(
        stream_ask(body.question, active, body.hybrid, body.model, body.api_key, history),
        media_type="text/event-stream",
    )


@router.get("/models")
def list_ollama_models():
    """Proxy Ollama /api/tags so the frontend can detect installed local models."""
    try:
        resp = httpx.get(
            f"{_OLLAMA_URL}/api/tags",
            timeout=httpx.Timeout(connect=3.0, read=5.0, write=2.0, pool=2.0),
        )
        if resp.status_code == 200:
            tags = resp.json().get("models", [])
            names = [m["name"] for m in tags if m.get("name")]
            return {"models": names}
    except Exception:
        pass
    return {"models": []}


def _doc_name(source: str) -> str:
    base = source.split("\\")[-1].split("/")[-1]
    return base.rsplit(".", 1)[0].strip()


@router.get("/suggestions")
def get_suggestions(collections: str | None = None):
    col_list = [c.strip() for c in collections.split(",")] if collections else None
    docs = list_documents(col_list)
    if not docs:
        return _FALLBACK_SUGGESTIONS

    names = list(dict.fromkeys(_doc_name(d["source"]) for d in docs if d.get("source")))
    if not names:
        return _FALLBACK_SUGGESTIONS

    results = []
    for name in names[:3]:
        short = name if len(name) <= 38 else name[:37] + "…"
        results.append({"title": f"Tóm tắt {short}", "subtitle": "Nội dung chính của tài liệu này"})

    fillers = [
        {"title": "Liệt kê tài liệu trong kho", "subtitle": f"Có {len(names)} tài liệu"},
        {"title": "So sánh các tài liệu", "subtitle": "Điểm giống và khác nhau"},
        {"title": "Thông tin quan trọng nhất", "subtitle": "Các điểm cần chú ý"},
    ]
    for f in fillers:
        if len(results) >= 4:
            break
        results.append(f)

    return results[:4]


class FollowUpsBody(BaseModel):
    question: str
    answer: str
    source_filenames: list[str] | None = None
    model: str | None = None
    api_key: str | None = None


@router.post("/follow-ups")
def follow_ups(body: FollowUpsBody):
    """Generate 3 follow-up question chips based on the latest Q+A and cited sources."""
    q = (body.question or "").strip()
    a = (body.answer or "").strip()
    if not q or not a:
        return {"suggestions": []}

    sources_hint = ""
    if body.source_filenames:
        sources_hint = " Tài liệu liên quan: " + ", ".join(body.source_filenames[:3]) + "."

    prompt = (
        "Dựa trên câu hỏi và câu trả lời sau, đề xuất 3 câu hỏi follow-up ngắn (mỗi câu ≤ 60 ký tự) "
        "mà người dùng có thể muốn hỏi tiếp về cùng chủ đề / tài liệu. "
        "Trả về CHỈ 3 câu hỏi, mỗi câu trên một dòng, không đánh số, không giải thích."
        f"{sources_hint}\n\n"
        f"Câu hỏi: {q}\nTrả lời: {a[:600]}\n\nFollow-up:"
    )
    raw = ""
    try:
        if body.api_key and body.api_key.startswith("gsk_"):
            resp = httpx.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {body.api_key}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 200,
                    "temperature": 0.5,
                },
                timeout=httpx.Timeout(connect=8.0, read=12.0, write=4.0, pool=4.0),
            )
            if resp.status_code == 200:
                raw = resp.json()["choices"][0]["message"]["content"].strip()
        else:
            resp = httpx.post(
                f"{_OLLAMA_URL}/api/generate",
                json={
                    "model": body.model or _OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": 200, "temperature": 0.5},
                },
                timeout=httpx.Timeout(connect=8.0, read=20.0, write=4.0, pool=4.0),
            )
            if resp.status_code == 200:
                raw = resp.json().get("response", "").strip()
    except Exception:
        return {"suggestions": []}

    lines = [re.sub(r'^[\d\.\)\-\*\s•]+', "", ln).strip().strip('"').strip("'").rstrip("?.") for ln in raw.split("\n")]
    suggestions = []
    for ln in lines:
        if 5 < len(ln) <= 80 and ln not in suggestions:
            suggestions.append(ln + "?")
            if len(suggestions) >= 3:
                break
    return {"suggestions": suggestions}
