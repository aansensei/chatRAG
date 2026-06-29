from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.application.retrieval.ask_question import stream_ask
from app.infrastructure.vector.supabase.repository import list_documents
from app.presentation.api.auth import get_collections

router = APIRouter(prefix="/chat", tags=["chat"])

_FALLBACK_SUGGESTIONS = [
    {"title": "Tóm tắt tài liệu", "subtitle": "Các điểm chính trong kho tài liệu"},
    {"title": "Thông tin công ty", "subtitle": "Ban lãnh đạo và cơ cấu tổ chức"},
    {"title": "Kết quả tài chính", "subtitle": "Doanh thu, lợi nhuận và chỉ số KPI"},
    {"title": "Kế hoạch nhân sự", "subtitle": "Tuyển dụng, đào tạo và phúc lợi"},
]


class QuestionRequest(BaseModel):
    question: str
    collections: list[str] | None = None
    collection: str = "default"
    hybrid: bool = False
    model: str | None = None
    api_key: str | None = None


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
    return StreamingResponse(
        stream_ask(body.question, active, body.hybrid, body.model, body.api_key),
        media_type="text/event-stream",
    )


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
