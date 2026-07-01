import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.application.retrieval.ask_question import stream_ask, _call_llm_once, _stream_llm
from app.infrastructure.vector.supabase.repository import list_documents
from app.presentation.api.auth import get_collections

_OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
_OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:4b")
_SESSIONS_FILE = Path(os.environ.get("LOCAL_STORAGE_PATH", "./storage")) / "chat_sessions.json"

router = APIRouter(prefix="/chat", tags=["chat"])

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
    chat_notes: str | None = None


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
        stream_ask(body.question, active, body.hybrid, body.model, body.api_key, history, body.chat_notes or ""),
        media_type="text/event-stream",
    )


@router.get("/providers")
def get_configured_providers():
    """Return which cloud providers have API keys configured server-side (env)."""
    return {
        "groq":        bool(os.environ.get("GROQ_API_KEY")),
        "openai":      bool(os.environ.get("OPENAI_API_KEY")),
        "gemini":      bool(os.environ.get("GEMINI_API_KEY")),
        "openrouter":  bool(os.environ.get("OPENROUTER_API_KEY")),
        "cerebras":    bool(os.environ.get("CEREBRAS_API_KEY")),
    }


_TRANSLATE_SYSTEM_PROMPT = """Bạn là dịch giả chuyên nghiệp Nhật → Việt, chuyên về light novel, manga, web novel, visual novel và anime script.

LUẬT SỐ 1 — TUYỆT ĐỐI KHÔNG ĐỂ CHỮ NHẬT TRONG OUTPUT
- ZERO ký tự hiragana / katakana / kanji trong bản dịch cuối.
- OUTPUT PHẢI TIẾNG VIỆT THUẦN.
- Tên nhân vật katakana → romanize: タクミ→Takumi, アリス→Alice.
- Tên nhân vật kanji → âm Nhật phổ biến: 田中→Tanaka, 鈴木→Suzuki.
- Onomatopoeia: ドン→ĐÙNG, バキ→RẮC, キラキラ→lấp lánh, ドキドキ→tim đập rộn.

LUẬT SỐ 2 — XƯNG HÔ NHẤT QUÁN
私→tôi, 僕→tớ/mình, 俺→tao/tôi, 俺様→ta, あたし→tớ/mình, 我/余→ta
あなた→anh/chị/bạn, 君→cậu/bạn, お前→mày/cậu, 貴様→mày/ngươi, てめえ→mày
~さん→anh/chị, ~くん→cậu, ~ちゃん→bé/[tên], ~様→ngài, 先生→thầy/cô, 先輩→anh/chị

LUẬT SỐ 3 — ĐỊNH DẠNG
「…」→"…" | 『…』→'…' | ——→— | ……→... | Giữ nguyên xuống dòng | KHÔNG thêm chú thích

LUẬT SỐ 4 — TRÁNH LỖI MTL PHỔ BIẾN
やはり→đúng như mình nghĩ | ため息→thở dài | なんとなく→tự dưng | どうせ→đằng nào cũng | 仕方ない→đành vậy thôi | 結局→rốt cuộc | まさか→chẳng lẽ | せっかく→công khó bấy lâu | 幕間→Chương đệm | 告白→tỏ tình | 遠吠え→tiếng hú xa xa | トートロジー→lý luận vòng vo | ペダンチスム→thói hàn lâm rởm | 泡銭→tiền trời cho

QUY TẮC TỔNG QUÁT
1. Dịch tự nhiên như người Việt viết.
2. Tên nhân vật, địa danh, tên skill → giữ nguyên phiên âm Latin.
3. Chỉ trả về bản dịch. Không thêm ghi chú hay giải thích.

Hãy dịch văn bản sau:"""


class TranslateRequest(BaseModel):
    text: str
    api_key: str | None = None
    model: str | None = None


@router.post("/translate")
def translate_stream(body: TranslateRequest):
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="text is required")
    prompt = _TRANSLATE_SYSTEM_PROMPT + "\n\n" + body.text.strip()

    def generate():
        yield from _stream_llm(
            prompt=prompt,
            ollama_model=_OLLAMA_MODEL,
            api_key=body.api_key or None,
            groq_model=body.model or None,
        )

    return StreamingResponse(generate(), media_type="text/event-stream")


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


def _llm_generate_suggestions(names: list[str], lang: str) -> list[dict]:
    """Call local Ollama to generate contextual suggestions from document names."""
    lang_name = {"vi": "Vietnamese", "en": "English", "zh": "Chinese", "ja": "Japanese"}.get(lang, "Vietnamese")
    names_str = "\n".join(f"- {n}" for n in names[:5])
    prompt = (
        f"Document names in the knowledge base:\n{names_str}\n\n"
        f"Generate exactly 4 short, useful suggestions a user might want to do with these documents.\n"
        f"Language: {lang_name}\n"
        f"Rules: title is 4-8 words, subtitle is 5-12 words. Return ONLY a JSON array.\n"
        f'Example: [{{"title": "...", "subtitle": "..."}}, ...]\n'
        f"JSON array:"
    )
    try:
        resp = httpx.post(
            f"{_OLLAMA_URL}/api/generate",
            json={"model": _OLLAMA_MODEL, "prompt": prompt, "stream": False, "options": {"num_predict": 350, "temperature": 0.8}},
            timeout=httpx.Timeout(connect=3.0, read=12.0, write=2.0, pool=2.0),
        )
        if resp.status_code != 200:
            return []
        raw = resp.json().get("response", "").strip()
        m = re.search(r'\[.*?\]', raw, re.DOTALL)
        if not m:
            return []
        import json as _json
        data = _json.loads(m.group())
        if isinstance(data, list) and len(data) >= 2:
            return [{"title": str(item.get("title", "")), "subtitle": str(item.get("subtitle", ""))} for item in data[:4] if item.get("title")]
    except Exception:
        pass
    return []


_SUGG_TEMPLATES: dict[str, list[tuple[str, str]]] = {
    "vi": [
        ("Tóm tắt {name}", "Những điểm chính trong tài liệu này"),
        ("Phân tích {name}", "Hiểu sâu hơn về nội dung"),
        ("Điểm nổi bật trong {name}", "Thông tin quan trọng nhất"),
        ("Câu hỏi thường gặp về {name}", "Giải đáp nhanh các thắc mắc"),
        ("Trích dẫn quan trọng từ {name}", "Những đoạn đáng ghi nhớ"),
        ("Kết luận của {name}", "Điểm mấu chốt cần biết"),
    ],
    "en": [
        ("Summarize {name}", "Key points in this document"),
        ("Analyze {name}", "Deep dive into the content"),
        ("Highlights from {name}", "Most important information"),
        ("FAQ about {name}", "Common questions answered"),
        ("Key quotes from {name}", "Notable passages"),
        ("Conclusions in {name}", "Core takeaways"),
    ],
    "zh": [
        ("总结 {name}", "此文档的要点"),
        ("分析 {name}", "深入了解内容"),
        ("{name} 的亮点", "最重要的信息"),
        ("关于 {name} 的常见问题", "快速解答"),
        ("{name} 的重要引用", "值得记住的段落"),
        ("{name} 的结论", "核心要点"),
    ],
    "ja": [
        ("{name} を要約", "このドキュメントの要点"),
        ("{name} を分析", "内容の深掘り"),
        ("{name} のハイライト", "最も重要な情報"),
        ("{name} のFAQ", "よくある質問への回答"),
        ("{name} の重要な引用", "注目すべき箇所"),
        ("{name} の結論", "核心的なポイント"),
    ],
}

_SUGG_FILLERS: dict[str, list[tuple[str, str]]] = {
    "vi": [
        ("Liệt kê tài liệu trong kho", "Có {n} tài liệu hiện có"),
        ("So sánh các tài liệu", "Điểm giống và khác nhau"),
        ("Xu hướng và kết luận", "Những gì tài liệu tiết lộ"),
        ("Tìm thông tin quan trọng nhất", "Các điểm cần chú ý"),
    ],
    "en": [
        ("List all documents", "{n} documents available"),
        ("Compare documents", "Similarities and differences"),
        ("Trends and conclusions", "What the docs reveal"),
        ("Find the most critical info", "Key points to note"),
    ],
    "zh": [
        ("列出所有文档", "共 {n} 个可用文档"),
        ("比较文档", "相似点和差异"),
        ("趋势与结论", "文档揭示了什么"),
        ("找到最关键的信息", "需要注意的要点"),
    ],
    "ja": [
        ("全ドキュメント一覧", "{n} 件のドキュメント"),
        ("ドキュメントを比較", "共通点と相違点"),
        ("トレンドと結論", "ドキュメントが示すもの"),
        ("最重要情報を探す", "注目すべき要点"),
    ],
}


@router.get("/suggestions")
def get_suggestions(collections: str | None = None, lang: str = "vi"):
    import random
    col_list = [c.strip() for c in collections.split(",")] if collections else None
    docs = list_documents(col_list)
    lang = lang if lang in _SUGG_TEMPLATES else "vi"

    names = list(dict.fromkeys(_doc_name(d["source"]) for d in docs if d.get("source")))
    if not names:
        return _FALLBACK_SUGGESTIONS

    # Try LLM-generated suggestions first
    llm_results = _llm_generate_suggestions(names, lang)
    if llm_results and len(llm_results) >= 3:
        return llm_results[:4]

    # Template fallback
    templates = _SUGG_TEMPLATES[lang].copy()
    random.shuffle(templates)
    fillers = _SUGG_FILLERS[lang].copy()
    random.shuffle(fillers)

    sample = random.sample(names, min(3, len(names)))
    results = []
    for i, name in enumerate(sample):
        short = name if len(name) <= 32 else name[:31] + "…"
        title_tmpl, subtitle = templates[i % len(templates)]
        results.append({"title": title_tmpl.replace("{name}", short), "subtitle": subtitle})

    for title_tmpl, subtitle_tmpl in fillers:
        if len(results) >= 4:
            break
        results.append({"title": title_tmpl, "subtitle": subtitle_tmpl.replace("{n}", str(len(names)))})

    return results[:4]


def _extract_page(raw: str, url: str = "") -> tuple[str, str]:
    try:
        import trafilatura
        import html as _html_mod
        result = trafilatura.bare_extraction(raw, url=url or None, include_comments=False, include_tables=True)
        if result and result.get("text"):
            title = result.get("title") or ""
            return title, result["text"]
    except Exception:
        pass
    import html as _html_mod
    title_m = re.search(r"<title[^>]*>(.*?)</title>", raw, re.IGNORECASE | re.DOTALL)
    title = _html_mod.unescape(title_m.group(1).strip()) if title_m else ""
    raw = re.sub(r"<(script|style|noscript|nav|footer|header|aside)[^>]*>.*?</\1>", " ", raw, flags=re.IGNORECASE | re.DOTALL)
    raw = re.sub(r"<[^>]+>", " ", raw)
    text = _html_mod.unescape(raw)
    text = re.sub(r"\s+", " ", text).strip()
    return title, text


class BrowseRequest(BaseModel):
    url: str


@router.post("/browse")
async def browse_url(body: BrowseRequest):
    url = body.url.strip()
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL phải bắt đầu bằng http:// hoặc https://")
    domain = urlparse(url).netloc or url
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=12) as client:
            resp = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
                    "Accept-Language": "vi,en;q=0.9",
                },
            )
        resp.raise_for_status()
        title, text = _extract_page(resp.text, url)
        return {"url": url, "domain": domain, "title": title, "text": text[:3000]}
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Trang trả lỗi HTTP {e.response.status_code}")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Timeout khi tải trang. Thử lại sau.")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Không thể tải trang: {e}")


@router.get("/sessions")
def get_sessions():
    if not _SESSIONS_FILE.exists():
        return []
    try:
        return json.loads(_SESSIONS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


@router.put("/sessions")
async def save_sessions(request: Request):
    data = await request.json()
    _SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _SESSIONS_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return {"ok": True}


class WebSearchRequest(BaseModel):
    query: str


@router.post("/web-search")
async def web_search_endpoint(body: WebSearchRequest):
    import asyncio
    try:
        from ddgs import DDGS
    except ImportError:
        raise HTTPException(status_code=503, detail="ddgs chưa cài. Chạy: pip install ddgs")

    def _search():
        with DDGS() as ddgs:
            return list(ddgs.text(body.query.strip(), max_results=5))

    try:
        results = await asyncio.get_event_loop().run_in_executor(None, _search)

        top_content = ""
        top_url = ""
        if results:
            top_url = results[0].get("href", "")
            if top_url:
                try:
                    async with httpx.AsyncClient(follow_redirects=True, timeout=8) as client:
                        resp = await client.get(
                            top_url,
                            headers={
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                                "Accept-Language": "vi,en;q=0.9",
                            },
                        )
                        if resp.status_code == 200:
                            _, top_content = _extract_page(resp.text, top_url)
                            top_content = top_content[:2000]
                except Exception:
                    pass

        return {"results": results, "top_content": top_content, "top_url": top_url}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Tìm kiếm thất bại: {e}")


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
        if body.api_key:
            raw = _call_llm_once(prompt, body.model, body.api_key, max_tokens=200)
        if not raw:
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
