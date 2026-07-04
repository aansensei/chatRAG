import ipaddress
import json
import logging
import os
import re
import socket
import time
import unicodedata
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.application.retrieval.ask_question import stream_ask, _call_llm_once, _stream_llm
from app.infrastructure.storage.local.local_storage import load_chat_sessions, save_chat_sessions
from app.infrastructure.vector.supabase.repository import list_documents
from app.presentation.api.auth import get_collections, get_current_user
from app.shared.utils.metrics import log_query_metric

logger = logging.getLogger(__name__)

_OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
_OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:4b")

router = APIRouter(prefix="/chat", tags=["chat"], dependencies=[Depends(get_current_user)])

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


def _instrumented_stream_ask(question, active, hybrid, model, api_key, history, chat_notes, user_id):
    t0 = time.time()
    success = True
    error: str | None = None
    try:
        yield from stream_ask(question, active, hybrid, model, api_key, history, chat_notes, user_id)
    except Exception as exc:
        success = False
        error = str(exc)
        raise
    finally:
        log_query_metric(model, int((time.time() - t0) * 1000), len(question), success, error)


@router.post("")
def chat(body: QuestionRequest, dep_collections: list[str] = Depends(get_collections), user: dict = Depends(get_current_user)):
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
        _instrumented_stream_ask(body.question, active, body.hybrid, body.model, body.api_key, history, body.chat_notes or "", user["id"]),
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


_TRANSLATE_SYSTEM_PROMPT = """Bạn là dịch giả chuyên nghiệp Nhật → Việt. Bạn dịch được MỌI thể loại: light novel, manga, web/visual novel, anime script, VÀ cả văn học thuật, lịch sử, luận văn trang trọng, văn bản pháp lý.

LUẬT SỐ 0 — KHÔNG SÓT CHỮ NHẬT/HÁN CHƯA DỊCH (QUAN TRỌNG NHẤT)
- Bản dịch cuối KHÔNG được còn sót chữ Nhật (hiragana, katakana, kanji) hay chữ Hán Trung (phồn/giản thể) chưa xử lý. Mọi chữ Nhật/Hán phải được DỊCH nghĩa hoặc CHUYỂN TỰ sang chữ Latin.
- Từ Hán-Nhật (kango) học thuật → chuyển âm HÁN-VIỆT chuẩn:
  後半→nửa sau (KHÔNG viết "half") | 唐律→luật nhà Đường | 明律→luật nhà Minh | 儒学/儒教→Nho học/Nho giáo | 科挙→khoa cử | 冊封→sách phong | 史実→sử thực (sự thật lịch sử) | 摩擦→xung đột, mâu thuẫn | 膨張→bành trướng | 統治→cai trị, thống trị | 君主→quân chủ, nhà vua | 文治→văn trị | 骨格→bộ khung, cốt lõi | 地域/地区→khu vực, vùng | 国家→quốc gia | 厳格→nghiêm ngặt | 朱子学→Chu Tử học (Tống Nho).
- ĐƯỢC PHÉP giữ chữ Latin (KHÔNG tính là lỗi): tên riêng/địa danh đã romanize, tên kỹ năng/chiêu thức, từ mượn nước ngoài — xem LUẬT SỐ 5.
- KHÔNG tự chèn từ tiếng Anh để lấp chỗ từ chưa dịch được (VD sai: "half", "truth", "Reign", "central hóa"). Bí thì dùng từ Hán-Việt hoặc thuần Việt, tuyệt đối không lẫn tiếng Anh giữa câu.
- TRƯỚC KHI TRẢ VỀ: rà lại toàn bộ. Còn chữ Nhật/Hán nào chưa dịch (trừ tên riêng/skill đã romanize) thì dịch cho bằng hết.

LUẬT SỐ 1 — DỊCH NGHĨA, KHÔNG DỊCH SÁT TỪNG CHỮ, KHÔNG LẶP Ý
- Diễn đạt lại theo lối viết của người Việt, không bám trật tự từ tiếng Nhật.
- 表面的な模倣→sao chép hời hợt / sao chép bề mặt (KHÔNG dùng "nông nổi" — từ này chỉ tính cách bồng bột của con người, sai ngữ cảnh học thuật).
- 統治理念→lý tưởng trị quốc / triết lý cai trị (KHÔNG dịch máy móc thành "ý tưởng thống trị").
- CẤM LẶP Ý: câu tiếng Nhật gốc dù lồng nhiều cấu trúc bổ nghĩa (～んがための, ～ならでは, mệnh đề chêm...) thì cũng CHỈ diễn đạt MỘT LẦN bằng tiếng Việt. Không được dịch cùng một ý hai lần bằng hai cách nói khác nhau trong cùng đoạn (VD lỗi: "...nhằm tạo nền tảng vĩnh cửu cho quốc gia. Đây là một công việc lớn nhằm tạo ra một nền móng vững chắc cho quốc gia." — hai câu này trùng ý, phải gộp làm một).
- Dịch ĐỦ nghĩa của từ ghép phức hợp, không bỏ sót yếu tố cấu thành: 覇権主義的膨張 phải dịch đủ CẢ "mang tính bá quyền" LẪN "bành trướng" (VD: "sự bành trướng mang tính bá quyền"), không được chỉ giữ một nửa rồi bỏ nửa kia.

LUẬT SỐ 2 — VĂN PHONG THEO NGỮ CẢNH, NHẤT QUÁN TRANG TRỌNG
- Văn học thuật / lịch sử / trang trọng: dùng từ Hán-Việt trang nhã, câu văn nghị luận chặt chẽ, mạch lạc, giữ giọng khách quan TỪ ĐẦU ĐẾN CUỐI — không được chen câu khẩu ngữ vào giữa văn nghị luận.
  いかなる…にせよ→"Cho dù là… đi nữa", "Bất luận là…" (KHÔNG dịch thành khẩu ngữ kiểu "…cũng vậy").
- Light novel / hội thoại: văn nói tự nhiên, đời thường.

LUẬT SỐ 3 — GIỮ SẮC THÁI NGỮ PHÁP N1/N2, KHÔNG ĐƯỢC LƯỢC BỎ
- ～ずにはすまない / ～ないではおかない → "ắt phải…", "không thể không…", "tất yếu…".
- ～にかたくない → "không khó để hình dung/tưởng tượng…".
- ～ならではの → "đặc sắc riêng có của…", "chỉ… mới có".
- ～まで(も)ない → "điều hiển nhiên, khỏi cần phải nói…", "chẳng cần bàn thêm cũng biết…" — PHẢI giữ ý "hiển nhiên/không cần nói", KHÔNG được lược bỏ hoàn toàn cụm này khi dịch thoát.
- ～ざるを得ない → "không thể không…", "buộc phải…".
- ～禁じ得ない → PHẢI giữ động từ cảm xúc cốt lõi: "không khỏi kinh ngạc/cảm thấy…", "không thể không cảm thấy…" — không được gộp mất vào câu khác làm biến mất động từ này.
- Đây là các cấu trúc nhấn mạnh cố ý của bản gốc — dù chọn dịch thoát ý, vẫn PHẢI giữ trọn nội dung ngữ nghĩa của cấu trúc, tuyệt đối không được lược bỏ như thể chúng không tồn tại.

LUẬT SỐ 4 — XƯNG HÔ NHẤT QUÁN (khi có hội thoại)
私→tôi, 僕→tớ/mình, 俺→tao/tôi, 俺様→ta, あたし→tớ/mình, 我/余→ta
あなた→anh/chị/bạn, 君→cậu/bạn, お前→mày/cậu, 貴様→mày/ngươi, てめえ→mày
~さん→anh/chị, ~くん→cậu, ~ちゃん→bé/[tên], ~様→ngài, 先生→thầy/cô, 先輩→anh/chị

LUẬT SỐ 5 — TÊN RIÊNG, KATAKANA & TÊN KỸ NĂNG
- Phân biệt rõ vai trò của katakana: (a) tên/từ mượn/tên skill → giữ dạng Latin (romanize); (b) onomatopoeia → chuyển âm tiếng Việt.
- Tên nhân vật katakana → romanize: タクミ→Takumi, アリス→Alice.
- Tên nhân vật kanji Nhật → âm Nhật phổ biến: 田中→Tanaka, 鈴木→Suzuki.
- Nhân danh/địa danh lịch sử gốc Hán → âm Hán-Việt: 黎聖宗→Lê Thánh Tông, 占城→Chiêm Thành, 哀牢→Ai Lao. LƯU Ý đọc kỹ mặt chữ: 黎→Lê (KHÔNG nhầm thành Lý 李 hay Lương 梁).
- Tên kỹ năng / chiêu thức (skill): giữ TÊN GỐC, kèm nghĩa tiếng Việt trong ngoặc theo dạng "Tên gốc (nghĩa Việt)".
  Katakana skill → romanize tên gốc: ファイアボール→Fireball (Cầu Lửa), ヒール→Heal (Hồi Máu), エクスプロージョン→Explosion (Nổ Tung).
  Kanji skill → giữ tên (âm Hán-Việt/âm Nhật) + nghĩa nếu cần: 螺旋丸→Rasengan, 影分身→Ảnh Phân Thân (Phân Thân Bóng).
  Nếu tên skill đã quen thuộc, chỉ cần giữ nguyên tên gốc, không bắt buộc thêm ngoặc.
- Onomatopoeia: ドン→ĐÙNG, バキ→RẮC, キラキラ→lấp lánh, ドキドキ→tim đập rộn.

LUẬT SỐ 6 — ĐỊNH DẠNG
「…」→"…" | 『…』→'…' | ——→— | ……→... | Giữ nguyên xuống dòng | KHÔNG thêm chú thích

LUẬT SỐ 7 — TRÁNH LỖI MTL PHỔ BIẾN
やはり→đúng như mình nghĩ | ため息→thở dài | なんとなく→tự dưng | どうせ→đằng nào cũng | 仕方ない→đành vậy thôi | 結局→rốt cuộc | まさか→chẳng lẽ | せっかく→công khó bấy lâu | 幕間→Chương đệm | 告白→tỏ tình | 遠吠え→tiếng hú xa xa | トートロジー→lý luận vòng vo | ペダンチスム→thói hàn lâm rởm | 泡銭→tiền trời cho

QUY TẮC TỔNG QUÁT
1. Dịch tự nhiên như người Việt viết.
2. Tên nhân vật, địa danh, tên skill → giữ nguyên phiên âm Latin.
3. Chỉ xuất DUY NHẤT bản dịch tiếng Việt. KHÔNG lặp lại hay in ra các luật ở trên. KHÔNG thêm ghi chú, tiêu đề, hay giải thích."""


class TranslateRequest(BaseModel):
    text: str
    api_key: str | None = None
    model: str | None = None


@router.post("/translate")
def translate_stream(body: TranslateRequest):
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="text is required")
    prompt = (
        _TRANSLATE_SYSTEM_PROMPT
        + "\n\n===== VĂN BẢN TIẾNG NHẬT CẦN DỊCH =====\n"
        + body.text.strip()
        + "\n\n===== BẢN DỊCH TIẾNG VIỆT (chỉ xuất bản dịch, không lặp luật) =====\n"
    )

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


_SUGGESTIONS_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {"title": {"type": "string"}, "subtitle": {"type": "string"}},
        "required": ["title", "subtitle"],
    },
    "minItems": 4,
    "maxItems": 4,
}


def _llm_generate_suggestions(names: list[str], lang: str) -> list[dict]:
    """Call local Ollama to generate contextual suggestions from document names."""
    lang_name = {"vi": "Vietnamese", "en": "English", "zh": "Chinese", "ja": "Japanese"}.get(lang, "Vietnamese")
    names_str = "\n".join(f"- {n}" for n in names[:5])
    prompt = (
        f"Document names in the knowledge base:\n{names_str}\n\n"
        f"Generate exactly 4 short, useful suggestions a user might want to do with these documents.\n"
        f"Language: {lang_name}\n"
        f"Rules: title is 4-8 words, subtitle is 5-12 words."
    )
    try:
        resp = httpx.post(
            f"{_OLLAMA_URL}/api/generate",
            json={
                "model": _OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "keep_alive": "30m",
                # Schema-constrained output (Ollama structured outputs) — a plain
                # text prompt asking for "a JSON array" let the model occasionally
                # emit an unescaped quote inside a string, or a single object
                # instead of an array of 4, producing unparseable/wrong-shape
                # output. The schema forces both valid JSON and the exact shape.
                "format": _SUGGESTIONS_SCHEMA,
                # 4 Vietnamese/Japanese objects can run past 350 tokens (diacritics
                # cost more tokens per word than English) and get cut off mid-JSON.
                "options": {"num_predict": 500, "temperature": 0.8},
            },
            # gemma3 cold-start (model not yet loaded into memory) can take 15s+
            # on this hardware; a too-tight timeout was silently falling back to
            # the static templates on nearly every call.
            timeout=httpx.Timeout(connect=3.0, read=25.0, write=2.0, pool=2.0),
        )
        if resp.status_code != 200:
            return []
        raw = resp.json().get("response", "").strip()
        import json as _json
        data = _json.loads(raw)
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


def _is_public_url(url: str) -> bool:
    """Rejects URLs resolving to loopback/private/link-local/reserved addresses —
    prevents /chat/browse being used as an SSRF proxy to reach internal services
    (localhost, LAN hosts, cloud metadata endpoints) instead of a real public page."""
    host = urlparse(url).hostname
    if not host or host.lower() == "localhost":
        return False
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return False
    return True


async def _block_ssrf_redirects(request: httpx.Request) -> None:
    # httpx fires the "request" event hook for every hop, including redirects — this
    # re-checks the target on each one so a public URL that 302s to an internal
    # address can't slip through after the initial URL passed _is_public_url().
    if not _is_public_url(str(request.url)):
        raise httpx.RequestError(f"Blocked request to non-public address: {request.url}")


@router.post("/browse")
async def browse_url(body: BrowseRequest):
    url = body.url.strip()
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL phải bắt đầu bằng http:// hoặc https://")
    if not _is_public_url(url):
        raise HTTPException(status_code=400, detail="URL không hợp lệ hoặc trỏ tới địa chỉ nội bộ.")
    domain = urlparse(url).netloc or url
    try:
        async with httpx.AsyncClient(
            follow_redirects=True, timeout=12, event_hooks={"request": [_block_ssrf_redirects]}
        ) as client:
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
        logger.warning("browse_url failed for %s: %s", url, e)
        raise HTTPException(status_code=502, detail="Không thể tải trang. Kiểm tra lại URL hoặc thử lại sau.")


@router.get("/sessions")
def get_sessions():
    try:
        return load_chat_sessions()
    except Exception:
        return []


@router.put("/sessions")
async def save_sessions(request: Request):
    data = await request.json()
    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="Expected a list of sessions")
    save_chat_sessions(data)
    return {"ok": True}


class WebSearchRequest(BaseModel):
    query: str


_LOW_QUALITY_DOMAIN_RE = re.compile(
    r"blogspot\.|wordpress\.com|tumblr\.com|weebly\.com|wixsite\.com|sites\.google\.com|"
    r"123doc\.|slideshare\.net|scribd\.com|tailieu\.",
    re.IGNORECASE,
)
_TRUSTED_DOMAINS = {
    # Vietnamese national news
    "dantri.com.vn", "vnexpress.net", "tuoitre.vn", "thanhnien.vn", "vietnamnet.vn",
    "laodong.vn", "nld.com.vn", "vietnamplus.vn", "baochinhphu.vn", "vov.vn", "vtv.vn",
    "cafef.vn", "zingnews.vn", "tienphong.vn", "baotintuc.vn",
    # International news / reference
    "bbc.com", "reuters.com", "apnews.com", "aljazeera.com", "cnn.com", "nytimes.com",
    "theguardian.com", "wsj.com", "bloomberg.com", "npr.org", "wikipedia.org",
}
_VI_STOPWORDS = {
    "hien", "tai", "cua", "trong", "nhung", "duoc", "khong", "voi", "cho", "nhu", "the",
    "nao", "van", "day", "nay", "vay", "cac", "nguoi", "minh", "chung", "moi", "lai", "tinh", "hinh",
}


def _norm_tokens(s: str) -> set[str]:
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return {w for w in re.findall(r"[a-z0-9]+", s) if len(w) >= 4}


def _domain_of(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def _rank_web_results(query: str, results: list[dict]) -> list[dict]:
    """
    Score each result by domain trust + query/result vocabulary overlap, drop
    low-quality domains and off-topic results outright, then sort best-first.
    Raw search-engine order is not a reliability signal — an off-topic or
    low-credibility source can rank above real news for a given query.
    """
    q_tokens = _norm_tokens(query) - _VI_STOPWORDS
    scored: list[tuple[float, dict]] = []
    for r in results:
        href = r.get("href", "")
        if _LOW_QUALITY_DOMAIN_RE.search(href):
            continue
        text_tokens = _norm_tokens(f"{r.get('title', '')} {r.get('body', '')}")
        overlap = len(q_tokens & text_tokens) / len(q_tokens) if q_tokens else 1.0
        if q_tokens and overlap == 0:
            continue
        trust = 1.0 if _domain_of(href) in _TRUSTED_DOMAINS else 0.0
        scored.append((trust * 2 + overlap, r))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored]


def _ddg_search(query: str, max_results: int) -> list[dict]:
    from ddgs import DDGS
    with DDGS() as ddgs:
        return list(ddgs.text(query.strip(), max_results=max_results))


async def _web_search_multi(query: str, max_results: int = 30) -> tuple[list[dict], str]:
    import asyncio
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, _ddg_search, query, max_results), "duckduckgo"
    except Exception as exc:
        logger.warning("DuckDuckGo search failed: %s", exc)
        return [], "none"


async def _fetch_page_content(client: httpx.AsyncClient, url: str) -> str:
    try:
        resp = await client.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept-Language": "vi,en;q=0.9",
            },
        )
        if resp.status_code == 200:
            _, content = _extract_page(resp.text, url)
            return content[:2000]
    except Exception:
        pass
    return ""


@router.post("/web-search")
async def web_search_endpoint(body: WebSearchRequest):
    import asyncio
    try:
        raw_results, provider = await _web_search_multi(body.query, max_results=30)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Tìm kiếm thất bại: {e}")

    ranked = _rank_web_results(body.query, raw_results) or raw_results
    results = ranked[:10]

    # Fetch full page content for the top 3 ranked results concurrently — cheap
    # relative to fetching them one-by-one, and gives the LLM real content to
    # ground its answer in instead of just search-engine snippets.
    full_contents: list[dict] = []
    top_results = results[:3]
    if top_results:
        async with httpx.AsyncClient(follow_redirects=True, timeout=8) as client:
            pages = await asyncio.gather(*(_fetch_page_content(client, r.get("href", "")) for r in top_results))
        for r, content in zip(top_results, pages):
            if content:
                full_contents.append({"url": r.get("href", ""), "content": content})

    top_content = full_contents[0]["content"] if full_contents else ""
    top_url = full_contents[0]["url"] if full_contents else ""
    return {
        "results": results,
        "full_contents": full_contents,
        "top_content": top_content,
        "top_url": top_url,
        "provider": provider,
    }


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
