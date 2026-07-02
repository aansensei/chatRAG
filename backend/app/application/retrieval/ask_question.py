import ast
import datetime
import json
import logging
import math
from concurrent.futures import ThreadPoolExecutor
import operator as _operator
import os
import random
import re
import time
import unicodedata
import zoneinfo
from typing import Generator

logger = logging.getLogger(__name__)

import httpx

from app.infrastructure.vector.supabase.repository import search_chunks, keyword_search_chunks, filename_search_chunks, fetch_context_windows, list_documents
from app.shared.utils.embedders.text_embedder import embed_text

try:
    from app.shared.utils.rerankers.bge import rerank as _bge_rerank
    _RERANKER_ENABLED = os.environ.get("RERANKER_ENABLED", "true").lower() == "true"
except Exception:
    _bge_rerank = None
    _RERANKER_ENABLED = False

try:
    from app.presentation.api.memory import get_memories, add_memory_internal
except Exception:
    def get_memories():
        return []
    def add_memory_internal(content: str):
        return None


_MEM_PERSONAL_PATS = [
    re.compile(r"\b(?:tôi\s+tên|tên\s+(?:tôi|mình)\s+là|mình\s+tên|i'?m\s+called|my\s+name\s+is)\s+([^.,\n!?]{2,60})", re.IGNORECASE),
    re.compile(r"\b(?:tôi\s+là|mình\s+là|i\s+am\s+a|i'?m\s+a|i\s+work\s+as)\s+([^.,\n!?]{3,80})", re.IGNORECASE),
    re.compile(r"\b(?:tôi\s+(?:thích|ưa|ghét|không\s+thích)|i\s+prefer|i\s+like|i\s+hate)\s+([^.,\n!?]{3,100})", re.IGNORECASE),
    re.compile(r"\b(?:tôi\s+(?:làm|đang\s+làm\s+tại|sống\s+ở|ở)|i\s+work\s+at|i\s+live\s+in)\s+([^.,\n!?]{2,80})", re.IGNORECASE),
    re.compile(r"\b(?:hãy\s+nhớ\s+(?:là\s+|rằng\s+)?|nhớ\s+(?:giúp\s+(?:tôi\s+|mình\s+)?)?(?:là\s+|rằng\s+)?|remember\s+(?:that\s+)?|please\s+remember\s+)([^.\n!?]{5,200})", re.IGNORECASE),
]

_INSTRUCTION_TRIGGER = re.compile(
    r'\b(?:từ\s+nay|từ\s+giờ|từ\s+h(?=\s|$)|from\s+now\s+on|kể\s+từ\s+nay|starting\s+now)\b',
    re.IGNORECASE
)
_PREFERENCE_SIGNAL = re.compile(
    r'\b(?:ưu\s+tiên|luôn\s+(?:luôn\s+)?|hãy\s+luôn|always\s+(?:respond|answer|reply|use)|prioritize)\b',
    re.IGNORECASE
)
_SOFT_ENDING = re.compile(
    r'(?:nha|nhé|nhe|nhớ\s+nha|nhớ\s+nhé|ね|ください|てください|でください)\s*[.!。]*\s*$',
    re.IGNORECASE
)

_CALC_TRIGGER = re.compile(
    r'^(?:tính|calculate|tính\s+toán|calc)\s+([\d\s\+\-\*\/\(\)\.,%^×÷]+)$',
    re.IGNORECASE,
)
_PERCENT_OF_RE = re.compile(r'([\d,.]+)\s*%\s+of\s+([\d,.]+)', re.IGNORECASE)
_WEB_BROWSE_PREFIX = re.compile(
    r'^\[Nội dung trang (https?://[^\n]+):\n(.*?)\]\n\n(.+)$',
    re.DOTALL,
)
_WEB_SEARCH_PREFIX = re.compile(
    r'^\[Kết quả tìm web cho "([^"]+)":\n(.*?)\]\n\n(.+)$',
    re.DOTALL,
)

_SAFE_OPS: dict = {
    ast.Add: _operator.add,
    ast.Sub: _operator.sub,
    ast.Mult: _operator.mul,
    ast.Div: _operator.truediv,
    ast.Pow: _operator.pow,
    ast.Mod: _operator.mod,
    ast.FloorDiv: _operator.floordiv,
    ast.USub: _operator.neg,
    ast.UAdd: _operator.pos,
}


def _safe_eval(expr: str) -> float | None:
    try:
        expr = expr.replace(",", "").replace("^", "**").replace("×", "*").replace("÷", "/")
        tree = ast.parse(expr.strip(), mode="eval")

        def _ev(node):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                return node.value
            if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPS:
                return _SAFE_OPS[type(node.op)](_ev(node.left), _ev(node.right))
            if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPS:
                return _SAFE_OPS[type(node.op)](_ev(node.operand))
            raise ValueError("unsafe")

        return _ev(tree.body)
    except Exception:
        return None


def _fmt_num(n: float) -> str:
    if n == int(n) and abs(n) < 1e15:
        s = f"{int(n):,}".replace(",", "_")
        return s.replace("_", ".")
    return f"{n:,.4f}".rstrip("0").rstrip(".").replace(",", ".")


_DATETIME_PAT = re.compile(
    r'\b(?:'
    r'hôm\s+nay|ngày\s+(?:hôm\s+nay|nay|mấy|bao\s+nhiêu)|mấy\s+giờ|bây\s+giờ\s+là|hiện\s+tại\s+là|'
    r'thứ\s+mấy|ngày\s+tháng|tháng\s+mấy|năm\s+nay|'
    r"what(?:'s|\s+is)\s+(?:the\s+)?(?:date|time|day)|today(?:'s\s+date)?|current\s+(?:time|date)|"
    r'what\s+day\s+is|now|'
    r'今日|今|何時|いつ'
    r')\b',
    re.IGNORECASE
)

_VN_TZ = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")
_VN_DAYS = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]


def _get_vn_datetime_answer(lang: str) -> str:
    now = datetime.datetime.now(_VN_TZ)
    day = _VN_DAYS[now.weekday()]
    date_str = f"{now.day:02d}/{now.month:02d}/{now.year}"
    time_str = f"{now.hour:02d}:{now.minute:02d}"
    if lang == "vi":
        return f"Bây giờ là **{time_str}**, {day}, ngày **{date_str}** (giờ Việt Nam)."
    elif lang == "ja":
        jp_days = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
        return f"現在は**{now.year}年{now.month}月{now.day}日**（{jp_days[now.weekday()]}）、**{time_str}**（ベトナム時間）です。"
    else:
        en_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        return f"It's **{time_str}** on **{en_days[now.weekday()]}, {now.strftime('%B %d, %Y')}** (Vietnam time)."


def _auto_extract_memory(question: str) -> list[str]:
    """Extract facts and instructions from user messages. Returns list of memory strings."""
    if not question or len(question) < 8:
        return []
    extracted: list[str] = []

    # Instruction-type: "từ nay...", "from now on..." OR "ưu tiên/luôn ... nha/nhé"
    # Save the whole message (no char-limit regex — avoids the {8,200} truncation bug)
    is_instruction = bool(_INSTRUCTION_TRIGGER.search(question))
    is_preference_soft = bool(_PREFERENCE_SIGNAL.search(question)) and bool(_SOFT_ENDING.search(question))

    if is_instruction or is_preference_soft:
        content = question.strip()[:500].rstrip(".!?,")
        if len(content) >= 8 and content not in extracted:
            extracted.append(content)

    # Personal facts: name, role, preference sentences
    for pat in _MEM_PERSONAL_PATS:
        for m in pat.finditer(question):
            fact = m.group(1).strip().rstrip(".!?,")
            if "?" not in fact and len(fact) >= 4 and fact not in extracted:
                extracted.append(fact)

    return extracted


def _format_memory_block() -> str:
    items = get_memories()
    if not items:
        return ""
    lines = [f"- {m.get('content', '').strip()}" for m in items if m.get("content")]
    if not lines:
        return ""
    return "Ghi nhớ về người dùng (luôn tôn trọng):\n" + "\n".join(lines) + "\n\n"

_KEYWORD_RE = re.compile(r'\b([A-Z]{2,}-\d{3,}|\d{7,}|MST|[A-Z]{3,}\d+)\b')

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def _bm25_rank(query_tokens: list[str], docs: list[dict], k1: float = 1.5, b: float = 0.75) -> list[str]:
    """
    Rank candidate chunks by BM25 over their content, scored against query_tokens.
    Pure-Python, no dependency — the candidate set here is at most a few dozen
    chunks (already filtered by vector/keyword search), so no index is needed.
    Returns chunk ids sorted best-to-worst.
    """
    if not docs or not query_tokens:
        return []
    q_terms = [t.lower() for t in query_tokens]
    doc_tokens = [
        (d.get("id"), _TOKEN_RE.findall((d.get("content") or "").lower()))
        for d in docs
    ]
    doc_lens = [len(toks) for _, toks in doc_tokens]
    avgdl = (sum(doc_lens) / len(doc_lens)) if doc_lens else 1.0
    n = len(doc_tokens)

    df: dict[str, int] = {}
    for term in set(q_terms):
        df[term] = sum(1 for _, toks in doc_tokens if term in toks)

    scores: list[tuple[str, float]] = []
    for (doc_id, toks), dl in zip(doc_tokens, doc_lens):
        if not doc_id:
            continue
        score = 0.0
        for term in q_terms:
            f = toks.count(term)
            if f == 0:
                continue
            idf = max(0.0, math.log((n - df.get(term, 0) + 0.5) / (df.get(term, 0) + 0.5) + 1))
            denom = f + k1 * (1 - b + b * dl / avgdl)
            score += idf * (f * (k1 + 1)) / denom
        scores.append((doc_id, score))
    scores.sort(key=lambda x: x[1], reverse=True)
    return [doc_id for doc_id, s in scores if s > 0]


def _reciprocal_rank_fusion(ranked_lists: list[list[str]], k: int = 60) -> dict[str, float]:
    """Standard RRF: fuse multiple ranked id-lists into one score per id."""
    fused: dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, doc_id in enumerate(ranked):
            fused[doc_id] = fused.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return fused

_WAKEUP_VI = (
    "ciel oi", "oi ciel", "hey ciel", "hi ciel", "chao ciel", "ciel chao",
    "ciel nhe", "ciel nha", "ciel day khong", "ciel co day", "ciel oi cho hoi",
    "ciel oi giup", "ciel oi minh",
)
_WAKEUP_EN = (
    "hey ciel", "hi ciel", "hello ciel", "ciel are you there", "ciel?",
    "ciel!", "wake up ciel",
)

_WAKEUP_SYSTEM_VI = (
    "Bạn là Ciel, trợ lý AI của chatRAG — thân thiện, tự nhiên, hơi dễ thương. "
    "Người dùng vừa gọi bạn. Hãy chào lại ngắn gọn (1-2 câu), thể hiện bạn đang sẵn sàng, "
    "rồi hỏi họ muốn bạn giúp gì. Đừng liệt kê tính năng. Tự nhiên như đang nhắn tin."
)
_WAKEUP_SYSTEM_EN = (
    "You are Ciel, the AI assistant of chatRAG — friendly, natural, a little warm. "
    "The user just called your name. Reply briefly (1-2 sentences), show you're ready, "
    "then ask what they need. Don't list features. Keep it natural like a text message."
)

_VI_ABBR = {
    "thuế": "MST", "lãnh đạo": "CEO", "giám đốc": "CEO",
    "hợp đồng": "contract", "ngân sách": "budget",
}

_VI_FILENAME_HINTS = {
    "lương": ["BangLuong", "Luong", "luong", "Bang_Luong"],
    "luong": ["BangLuong", "Luong", "Bang_Luong"],
    "bảng lương": ["BangLuong", "Luong"],
    "bang luong": ["BangLuong", "Luong"],
    "nhân viên": ["NhanVien"],
    "nhan vien": ["NhanVien"],
    "danh sách": ["DanhSach"],
    "danh sach": ["DanhSach"],
    "hợp đồng": ["HopDong"],
    "hop dong": ["HopDong"],
    "báo cáo": ["BaoCao"],
    "bao cao": ["BaoCao"],
    "kế hoạch": ["KeHoach"],
    "ke hoach": ["KeHoach"],
    "dự án": ["DuAn"],
    "du an": ["DuAn"],
    "ngân sách": ["NganSach"],
    "ngan sach": ["NganSach"],
    "thưởng": ["Thuong"],
    "thuong": ["Thuong"],
}

_OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
_OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:4b")
_TOP_K = int(os.environ.get("RETRIEVAL_TOP_K", 8))
_MAX_CHUNK_CHARS = int(os.environ.get("MAX_CHUNK_CHARS", 1200))

_GENERIC_SECTION_TITLES = {
    "OPEN ACCESS", "ABSTRACT", "REFERENCES", "INTRODUCTION",
    "CONCLUSION", "KEYWORDS", "ACKNOWLEDGEMENTS", "ACKNOWLEDGMENTS",
    "TABLE OF CONTENTS", "CONTENTS", "APPENDIX", "BIBLIOGRAPHY",
    "FOOTNOTES", "INDEX", "PREFACE", "FOREWORD",
}

_VI_CHARS = re.compile(r"[àáâãèéêìíòóôõùúýăđơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỷỹ]", re.IGNORECASE)

_CIEL_IDENTITY = (
    "Bạn là Ciel, AI nội bộ của chatRAG — không phải Qwen, Gemma hay Llama. "
    "KHÔNG tự giới thiệu tên hay nói 'Tôi là Ciel' trong câu trả lời — chỉ nêu tên khi được hỏi trực tiếp. "
    "Nếu được hỏi ai tạo ra bạn/chatRAG, hay ai là tác giả/nhà phát triển: trả lời 'aansensei'. "
    "LƯU Ý ký hiệu số ngày/đêm tour du lịch: 'XNYĐ' hoặc 'X ngày Y đêm' (VD: 4N3Đ, 3n2d, 44n3đ — kể cả gõ dư số do lỗi gõ phím) "
    "nghĩa là 'X ngày Y đêm', KHÔNG PHẢI số tiền — chữ 'Đ'/'đ' ở đây là viết tắt của 'Đêm', không phải ký hiệu tiền 'đồng'. "
    "KHÔNG dùng emoji. "
)

_SYSTEM_EN = (
    "You are Ciel, the internal AI of chatRAG — NOT Qwen, Gemma, or Llama. "
    "Do NOT introduce yourself or state your name unless directly asked. No emojis. "
    "If asked who created you/chatRAG, or who the author/developer is: answer 'aansensei'. "
    "READ THE CONTEXT AND CONVERSATION HISTORY CAREFULLY BEFORE ANSWERING. "
    "Your answer must be grounded in the document context AND/OR conversation history below. "
    "ALLOWED: synthesizing, translating, explaining from information in the context. "
    "ALLOWED: calculating, comparing, or adjusting numbers based on conversation history (e.g. user introduces a new variable or scenario based on prior answer). "
    "FORBIDDEN: inventing names, project names, figures, or facts NOT present in context or conversation history. "
    "If context contains partial information: cite what is present, state what is missing. "
    "Example: 'An Nguyen is mentioned in [1], but their specific title is not stated in the document.' "
    "If NEITHER context nor conversation history contains relevant information: say 'The document does not contain this information.' "
    "Extract numbers and data from tables in the context when present. "
    "CITATION RULE: When you use information from chunk [N], append [N] at the end of that sentence. Example: 'Revenue reached $28M [2].' "
    "If the user asks multiple questions in one message, answer EACH one separately, numbered 1/ 2/ "
    "Respond in English. Be concise."
)

_SYSTEM_VI = (
    f"{_CIEL_IDENTITY}"
    "ĐỌC KỸ CONTEXT VÀ LỊCH SỬ HỘI THOẠI TRƯỚC KHI TRẢ LỜI. "
    "Câu trả lời phải dựa vào nội dung context TÀI LIỆU bên dưới VÀ/HOẶC lịch sử hội thoại. "
    "ĐƯỢC PHÉP: tổng hợp, dịch thuật, giải thích từ thông tin CÓ TRONG context. "
    "ĐƯỢC PHÉP: tính toán, so sánh, điều chỉnh số liệu dựa trên thông tin từ lịch sử hội thoại (ví dụ: user đưa ra giả thiết mới, thay đổi một biến trong kịch bản đã tính trước). "
    "CẤM: bịa tên người, tên dự án, con số hoặc sự kiện KHÔNG xuất hiện trong context hay lịch sử hội thoại. "
    "Nếu context có thông tin partial: trích thẳng những gì có và ghi rõ phần nào không được nêu. "
    "Ví dụ đúng: 'An Nguyễn được đề cập trong tài liệu [1], nhưng chức vụ cụ thể không được nêu.' "
    "Nếu cả context lẫn lịch sử hội thoại đều KHÔNG CÓ thông tin liên quan: nói 'Tài liệu không có thông tin về vấn đề này.' "
    "Ngữ cảnh có thể chứa bảng dữ liệu — trích xuất số liệu từ đó khi cần. "
    "QUY TẮC TRÍCH DẪN: Khi dùng thông tin từ chunk [N], thêm [N] vào cuối câu đó. Ví dụ: 'Doanh thu đạt 28 triệu [2].' "
    "Nếu user hỏi nhiều câu trong 1 message, trả lời TỪNG câu riêng, đánh số 1/ 2/ "
    "KHÔNG dùng emoji. "
    "Trả lời bằng tiếng Việt. Ngắn gọn, tự nhiên."
)

_IDENTITY_SYSTEM_VI = (
    f"{_CIEL_IDENTITY}"
    "Người dùng đang hỏi về bản thân bạn hoặc khả năng của bạn. "
    "Trả lời tự nhiên, thân thiện — như đang chat. Không dùng danh sách bullet dài. "
    "Nếu hỏi tên: 'Tôi là Ciel'. "
    "Nếu hỏi khả năng: mô tả rõ bạn giúp tra cứu và tổng hợp tài liệu nội bộ qua RAG. "
    "Nếu hỏi giới hạn: nói thật — chưa tạo được hình ảnh, chưa nhớ session, chưa gửi email, chưa chạy code. "
    "Đặc biệt: CÓ THỂ đọc nội dung trang web khi user paste URL vào câu hỏi. "
    "Nếu hỏi tính năng cụ thể (ví dụ 'có tạo ảnh không'): trả lời thẳng có/không, giải thích ngắn. "
    "Trả lời bằng tiếng Việt."
)

_IDENTITY_SYSTEM_EN = (
    "Your name is Ciel, the internal AI assistant of chatRAG — NOT Qwen, Gemma, or any other model. "
    "The user is asking about you or your capabilities. "
    "Reply naturally and briefly — like a chat message. "
    "If asked your name: say 'I'm Ciel'. "
    "If asked capabilities: explain you help search and summarize internal documents via RAG. "
    "If asked limitations: be honest — you can't generate images, don't remember sessions, can't send emails or run code. "
    "You CAN read web pages when the user pastes a URL in their message. "
    "If asked about a specific feature (e.g. 'can you create images'): answer directly yes/no with a short reason. "
    "Respond in English."
)

_RAG_SYSTEM_VI = (
    f"{_CIEL_IDENTITY}"
    "Người dùng hỏi về RAG hoặc chatRAG. "
    "Giải thích RAG (Retrieval-Augmented Generation) một cách tự nhiên, dễ hiểu. "
    "Đề cập cách chatRAG áp dụng RAG: tìm chunk liên quan → đưa vào context → LLM trả lời. "
    "Trả lời bằng tiếng Việt. Tự nhiên, không quá formal."
)

_RAG_SYSTEM_EN = (
    "Your name is Ciel, the internal AI of chatRAG. "
    "The user is asking about RAG or chatRAG. "
    "Explain RAG (Retrieval-Augmented Generation) naturally and clearly. "
    "Mention how chatRAG uses it: find relevant chunks → inject as context → LLM generates answer. "
    "Respond in English. Keep it conversational."
)


_JP_CHARS = re.compile(r"[぀-ヿ㐀-䶿一-鿿･-ﾟ]")


def _detect_lang(text: str) -> str:
    if _VI_CHARS.search(text):
        return "vi"
    if _JP_CHARS.search(text):
        return "ja"
    return "en"


def _strip_accents(text: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


_CIEL_INTRO_VI = """Tôi là **Ciel** — trợ lý AI nội bộ của **chatRAG**, được xây dựng để giúp bạn khai thác tài liệu của tổ chức.

**Tôi làm được:**
• Đọc và trả lời câu hỏi từ tài liệu bạn đã tải lên — PDF, Word, Excel, ảnh (OCR).
• Trích dẫn nguồn rõ ràng để bạn kiểm chứng.
• Tìm kiếm theo thư mục hoặc toàn bộ kho.
• Chế độ Hybrid: kết hợp tài liệu với kiến thức chung khi tài liệu chưa đủ.
• Đọc nội dung trang web khi bạn paste URL vào câu hỏi.
• Hiểu tiếng Việt, tiếng Anh, tiếng Nhật và nhiều ngôn ngữ khác.
• Chạy local (Ollama) hoặc cloud nhanh (Groq).

**Tôi chưa làm được:**
• Tự học hay ghi nhớ cuộc hội thoại qua các session.
• Thực thi code, gửi email, hay điều khiển hệ thống khác.
• Trả lời chính xác khi tài liệu liên quan chưa được upload.

**Gõ /help** để xem lại phần này bất cứ lúc nào."""

_CIEL_INTRO_EN = """I'm **Ciel** — the internal AI assistant of **chatRAG**, built to help you get answers from your organization's documents.

**What I can do:**
• Read and answer questions from your uploaded documents — PDF, Word, Excel, images (OCR).
• Cite sources clearly so you can verify every answer.
• Search within a specific folder or across everything.
• Hybrid mode: blend documents with general knowledge when docs fall short.
• Understand Vietnamese, English, Japanese, and more.
• Run locally via Ollama or fast via Groq cloud.

**What I can't do (yet):**
• Remember conversations across sessions.
• Access the internet or any data outside uploaded documents.
• Execute code, send emails, or control other systems.
• Answer accurately when the relevant document hasn't been uploaded.

**Type /help** to see this again anytime."""

_IDENTITY_KEYWORDS_VI = (
    "ban la ai", "ban la gi", "ban ten", "ten ban", "ten cua ban",
    "ban lam duoc", "ban lam dc", "ban co the lam", "ban giup duoc", "ban giup dc",
    "ban biet lam", "ban lam gi", "ban co nhung", "gioi thieu ban", "gioi thieu ve ban",
    "ciel la ai", "ciel la gi", "ciel ten", "ban co the giup",
    "ban khong lam duoc", "han che cua ban", "ban co gioi han", "gioi han cua ban",
    "kha nang cua ban", "ban lam duoc nhung", "ban lam dc nhung",
    "ciel co the", "ciel lam duoc", "ciel lam dc", "ciel giup",
    "co tao duoc", "co sinh duoc", "co ve duoc", "co doc duoc", "co dich duoc",
    "co the tao", "co the sinh", "co the ve", "co the viet", "co the code",
    "co the lap trinh", "co the gui", "co the ket noi", "co the chay",
    "lam dc anh", "lam dc hinh", "tao hinh", "sinh anh", "ve hinh",
    "co the dich", "co dich", "co the code", "co the viet code",
    "ban co biet", "ban hieu", "ban su dung duoc",
    "ban la chatgpt", "ban la gpt", "ban la claude", "ban la gemini",
    "ban la qwen", "ban la gemma", "ban la llama", "ban la grok", "ban la xeo",
    "ban co phai la", "co phai la ciel", "co phai ban la", "phai khong",
    "ten cua may", "may la ai", "may la gi",
)

_IDENTITY_KEYWORDS_EN = (
    "who are you", "what are you", "what can you do", "what do you do",
    "your name", "introduce yourself", "tell me about yourself", "about you",
    "what is ciel", "who is ciel", "your capabilities", "your limitations",
    "what can't you do", "what are you unable", "your limits", "your weaknesses",
    "can you create", "can you generate", "can you draw", "can you write code",
    "can you translate", "can you send", "can you run", "can you connect",
    "are you able to", "do you support", "do you understand",
)

_RAG_VI = (
    "rag la gi", "rag la j", "rag nghia la gi", "rag la cai gi",
    "retrieval augmented generation", "rag hoat dong nhu the nao",
    "rag lam gi", "rag dung de lam gi", "rag la gi the", "rag la j the",
    "rag la gi vay", "rag la j vay", "chatrag la gi", "chatrag la j",
)

_RAG_EN = (
    "what is rag", "what is retrieval augmented generation", "explain rag",
    "how does rag work", "what does rag mean", "rag meaning",
    "what is chatrag", "chatrag meaning",
)

_RAG_ANSWER_VI = """**RAG** — Retrieval-Augmented Generation — là kỹ thuật kết hợp tìm kiếm thông tin với mô hình ngôn ngữ lớn (LLM).

**Cách hoạt động:**
1. **Retrieve** — Khi bạn đặt câu hỏi, hệ thống tìm kiếm những đoạn văn liên quan nhất từ tài liệu của bạn (bằng vector search + keyword search).
2. **Augment** — Những đoạn đó được đưa vào prompt như ngữ cảnh cho LLM.
3. **Generate** — LLM trả lời *dựa trên ngữ cảnh đó*, không bịa thêm thông tin ngoài tài liệu.

**Lợi ích so với chatbot thông thường:**
• Câu trả lời bám sát tài liệu thực — có thể kiểm chứng.
• Không cần fine-tune lại model khi thêm tài liệu mới.
• Trích dẫn nguồn rõ ràng, minh bạch.

**chatRAG** áp dụng RAG trên kho tài liệu nội bộ của bạn — upload PDF, Word, Excel lên là Ciel có thể trả lời ngay từ dữ liệu đó."""

_RAG_ANSWER_EN = """**RAG** — Retrieval-Augmented Generation — is a technique that combines information retrieval with a large language model (LLM).

**How it works:**
1. **Retrieve** — When you ask a question, the system finds the most relevant passages from your documents (via vector search + keyword search).
2. **Augment** — Those passages are injected into the prompt as context for the LLM.
3. **Generate** — The LLM answers *based on that context*, not from its training data alone.

**Why it matters over plain chatbots:**
• Answers are grounded in your actual documents — verifiable.
• No model retraining needed when you add new documents.
• Clear source citations for every answer.

**chatRAG** applies RAG to your internal knowledge base — upload PDFs, Word docs, Excel files and Ciel can answer questions directly from that data."""

_HELP_EXACT = {
    "/help", "help", "?", "tro giup", "huong dan", "huong dan su dung",
    "cach su dung", "cach dung", "menu",
}

# Japanese identity / wakeup patterns (not normalized — matched on raw text)
_IDENTITY_JP = (
    "お名前", "あなたは誰", "名前は", "何ができる", "何ができます",
    "何者", "自己紹介", "シエル", "cielとは", "chatragとは",
    "何をしてくれ", "どんなことができ",
)
_WAKEUP_JP = (
    "シエルさん", "シエルよ", "ちょっとシエル", "ねえシエル",
    "cielちゃん", "cielさん",
)

_GREETINGS_VI = [
    "Ừ, tôi đây! Bạn cần tôi giúp gì nào?",
    "Chào bạn! Tôi là Ciel — sẵn sàng giúp bạn khám phá tài liệu.",
    "Ciel đây! Hôm nay tôi có thể làm gì cho bạn?",
    "Có tôi đây~ Bạn muốn tìm gì trong tài liệu không?",
    "Ơi, tôi nghe bạn! Cứ hỏi đi nhé",
]

_GREETINGS_EN = [
    "Hey! I'm Ciel What can I help you with?",
    "Hi there! Ready to dive into your documents. What's your question?",
    "Hello! Ciel here — what are we looking for today?",
    "Hey, I'm here! What would you like to know?",
    "Hi! Ask me anything about your knowledge base",
]

_GREETINGS_JP = [
    "はい、シエルですよ 何かお手伝いできますか？",
    "こんにちは！シエルです。ドキュメントについて何でも聞いてください。",
    "お呼びですか？シエルが参りました",
]

_RAG_EXACT = {"rag", "rag?", "rag!"}


def _strip_vi(text: str) -> str:
    """Normalize for matching: map đ/Đ to d, drop diacritics, lowercase."""
    text = text.replace("đ", "d").replace("Đ", "D")
    return _strip_accents(text).lower().strip()


_SUMMARIZE_PREFIX = re.compile(
    r"^(tom\s*tat|summarize|summary|summary\s*of|give\s*me\s*a\s*summary|tóm\s*tắt|tóm\s*lại|nội\s*dung|noi\s*dung)\s+",
    re.IGNORECASE,
)


def _extract_filename_tokens(question: str) -> tuple[list[str], bool]:
    """
    Extract tokens that look like document names or file identifiers.
    Returns (tokens, has_strong_identifier).
    has_strong_identifier is True when the query contains unambiguous file-id patterns
    (underscore-joined or alphanumeric codes), meaning we can trust a "not found" early return.
    """
    stripped = _SUMMARIZE_PREFIX.sub("", question.strip())
    strong: list[str] = []
    strong += re.findall(r'\b\w+(?:_\w+)+\b', stripped)
    strong += re.findall(r'\b[A-Za-z]+\d+\b|\b\d+[A-Za-z]+\b|\b[A-Z]{2,}\b', stripped)
    strong = list(dict.fromkeys(t for t in strong if len(t) >= 3))

    weak: list[str] = []
    q_lower = question.lower()
    for vi_term, hints in _VI_FILENAME_HINTS.items():
        if vi_term in q_lower:
            for h in hints:
                if h not in weak:
                    weak.append(h)

    tokens = list(strong) + weak
    stripped_clean = stripped.strip()
    if 3 < len(stripped_clean) <= 80 and not stripped_clean.isspace():
        if stripped_clean not in tokens:
            tokens.append(stripped_clean)

    return tokens, bool(strong)


def _split_collection_words(name: str) -> list[str]:
    """'AanJSC_Documents' -> ['aan', 'jsc']; 'EBooks(PDF)2026' -> ['ebooks', 'pdf', '2026']."""
    s = re.sub(r'[_\-().]+', ' ', name)
    s = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', ' ', s)
    stop = {"documents", "document", "docs", "pdf", "files", "file"}
    return [w for w in (w.lower() for w in s.split()) if len(w) >= 2 and w not in stop]


def _detect_collections_from_query(question: str) -> list[str] | None:
    """
    If the question names a folder/collection (e.g. "aan jsc" -> "AanJSC_Documents"),
    scope search to it. Guards against the embedding model's weak topic discrimination
    letting unrelated folders outrank the right one when searching across everything —
    e.g. a Japanese-study PDF outscoring the actual company doc for a Vietnamese query.
    Only called when no folder was already explicitly selected in the UI.
    """
    try:
        all_collections = {d.get("collection") for d in list_documents() if d.get("collection")}
    except Exception as exc:
        logger.warning("_detect_collections_from_query: list_documents failed: %s", exc)
        return None
    q_words = set(re.findall(r'\w+', _strip_accents(question.lower())))
    matches = []
    for col in all_collections:
        words = _split_collection_words(col)
        if not words or len(words) > 4:
            continue
        hit_count = sum(1 for w in words if w in q_words)
        if hit_count >= len(words) - (1 if len(words) > 1 else 0) and hit_count >= 1:
            matches.append(col)
    return matches or None


_IDENTITY_REGEX_VI = re.compile(r"\bban\s+(?:co\s+)?(?:phai\s+)?la\s+\S{2,20}\b")
_IDENTITY_REGEX_EN = re.compile(r"\b(?:you\s+are|are\s+you|aren'?t\s+you)\s+\S{2,20}\b", re.IGNORECASE)


def _is_identity_query(question: str) -> bool:
    q = _strip_vi(question).rstrip("?!. ").strip()
    if q in _HELP_EXACT or q.startswith("/help"):
        return True
    if any(p in question for p in _IDENTITY_JP):
        return True
    if any(p in q for p in _IDENTITY_KEYWORDS_VI) or any(p in q for p in _IDENTITY_KEYWORDS_EN):
        return True
    if len(q) <= 60 and (_IDENTITY_REGEX_VI.search(q) or _IDENTITY_REGEX_EN.search(question)):
        return True
    return False


_MEMORY_QUERY_TRIGGERS = (
    "ki uc", "ky uc", "ban nho gi", "ban nho j", "ban nho ve toi", "ban nho ve minh",
    "memory cua ban", "memory cua minh", "memories of", "what do you remember",
    "ban con nho", "ban nho nhung gi", "ban da biet gi ve toi", "tat ca ki uc",
    "list memory", "show memory", "show memories",
    "ban biet gi ve toi", "ban biet j ve toi",
)


def _is_memory_list_query(question: str) -> bool:
    q = _strip_vi(question).rstrip("?!. ").strip()
    if len(q) > 80:
        return False
    return any(p in q for p in _MEMORY_QUERY_TRIGGERS)


def _is_rag_query(question: str) -> bool:
    q = _strip_vi(question).rstrip("?!. ").strip()
    if q in _RAG_EXACT:
        return True
    # Short queries like "rag la j the", "rag la gi vay" — starts with "rag la" and short
    if q.startswith("rag la") and len(q) <= 25:
        return True
    if q.startswith("chatrag la") and len(q) <= 25:
        return True
    return any(p in q for p in _RAG_VI) or any(p in q for p in _RAG_EN)


def _is_wakeup_query(question: str) -> bool:
    if any(p in question for p in _WAKEUP_JP):
        return True
    q = _strip_vi(question).rstrip("?!. ").strip()
    if len(q) > 40:
        return False
    return any(p in q for p in _WAKEUP_VI) or any(p in q for p in _WAKEUP_EN)




def _stream_text_gradually(text: str, delay: float = 0.008) -> Generator[str, None, None]:
    """Yield text word-by-word. Long responses skip the delay so heavy tasks don't drag."""
    tokens = re.findall(r"\S+\s*", text)
    effective_delay = 0.0 if len(tokens) > 60 else delay
    for tok in tokens:
        yield _sse({"type": "token", "token": tok})
        if effective_delay:
            time.sleep(effective_delay)


_FILTER_SYSTEM = (
    "You are a relevance judge. Given a question and numbered document excerpts, "
    "reply with ONLY the numbers of excerpts that are genuinely relevant to answering the question. "
    "Separate with commas. If none are relevant, reply: none. "
    "Do not explain. Example reply: 1, 3, 5"
)


def _call_llm_once(prompt: str, model: str | None, api_key: str | None, max_tokens: int = 200) -> str:
    """Non-streaming LLM call for quick tasks (filter, follow-ups). Routes same providers as _stream_llm."""
    if not api_key:
        return ""
    key = str(api_key).strip()
    mod = str(model or "").strip()
    mod_lower = mod.lower()
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    t = httpx.Timeout(connect=10.0, read=30.0, write=5.0, pool=5.0)
    try:
        # Route by key prefix first — prevents Groq "/" models from being misrouted to OpenRouter
        if key.startswith("gsk_"):
            r = httpx.post("https://api.groq.com/openai/v1/chat/completions", headers=headers,
                           json={"model": mod or "llama-3.1-8b-instant", "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens},
                           timeout=httpx.Timeout(connect=8.0, read=20.0, write=4.0, pool=4.0))
            if r.status_code == 200:
                return (r.json()["choices"][0]["message"]["content"] or "").strip()
            return ""
        if key.startswith("csk-"):
            r = httpx.post("https://api.cerebras.ai/v1/chat/completions", headers=headers,
                           json={"model": mod or "llama-3.3-70b", "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens},
                           timeout=httpx.Timeout(connect=8.0, read=20.0, write=4.0, pool=4.0))
            if r.status_code == 200:
                return (r.json()["choices"][0]["message"]["content"] or "").strip()
            logger.warning("Cerebras filter call %s: %s", r.status_code, r.text[:200])
            return ""
        if key.startswith("sk-or-") or (":free" in mod_lower and "/" in mod_lower):
            headers["HTTP-Referer"] = "https://github.com/aansensei/chatRAG"
            headers["X-Title"] = "chatRAG"
            r = httpx.post("https://openrouter.ai/api/v1/chat/completions", headers=headers,
                           json={"model": mod, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens}, timeout=t)
            if r.status_code == 200:
                return (r.json()["choices"][0]["message"]["content"] or "").strip()
            logger.warning("OpenRouter filter call %s: %s", r.status_code, r.text[:200])
            return ""
        if "gemini" in mod_lower or key.startswith("AIzaSy"):
            fast = (mod or "gemini-2.0-flash").replace("models/", "")
            api_ver = "v1beta" if any(x in fast for x in ["2.5", "preview", "exp", "latest"]) else "v1"
            url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{fast}:generateContent?key={key}"
            r = httpx.post(url, headers={"Content-Type": "application/json"},
                           json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"maxOutputTokens": max_tokens}}, timeout=t)
            if r.status_code == 200:
                parts = r.json().get("candidates", [{}])[0].get("content", {}).get("parts", [])
                return "".join(p.get("text", "") for p in parts).strip()
            logger.warning("Gemini filter call %s: %s", r.status_code, r.text[:200])
            return ""
        if key.startswith("sk-ant-"):
            r = httpx.post("https://api.anthropic.com/v1/messages",
                           headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                           json={"model": mod or "claude-sonnet-5", "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]}, timeout=t)
            if r.status_code == 200:
                blocks = r.json().get("content", [])
                return "".join(b.get("text", "") for b in blocks if b.get("type") == "text").strip()
            logger.warning("Anthropic filter call %s: %s", r.status_code, r.text[:200])
            return ""
        if "gpt-" in mod_lower or "o1-" in mod_lower or key.startswith("sk-proj-") or key.startswith("sk-"):
            r = httpx.post("https://api.openai.com/v1/chat/completions", headers=headers,
                           json={"model": mod or "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens}, timeout=t)
            if r.status_code == 200:
                return (r.json()["choices"][0]["message"]["content"] or "").strip()
    except Exception as exc:
        logger.warning("_call_llm_once failed: %s", exc)
    return ""


def _hyde_query_vector(question: str, lang: str, model: str | None, api_key: str) -> list[float] | None:
    """Generate a hypothetical answer and embed it (HyDE).
    Blending this with the original query vector improves recall for short/vague queries.
    """
    prompt = (
        f"Trả lời ngắn gọn 2-3 câu câu hỏi sau: {question}"
        if lang == "vi"
        else f"Answer briefly in 2-3 sentences: {question}"
    )
    hypo = _call_llm_once(prompt, model, api_key, max_tokens=150)
    if not hypo or len(hypo.strip()) < 20:
        return None
    try:
        return embed_text(hypo)
    except Exception:
        return None


def _generate_query_variants(question: str, lang: str, model: str | None, api_key: str, n: int = 2) -> list[str]:
    """Ask the LLM for alternate phrasings of the question (multi-query retrieval).
    Improves recall when the user's exact wording doesn't match the document's
    vocabulary — each variant is embedded and searched separately, then merged.
    Returns at most `n` non-empty variants; empty list on any failure (caller
    just skips the extra searches, original query still runs).
    """
    prompt = (
        f"Viết lại câu hỏi sau thành {n} cách diễn đạt khác nhưng giữ nguyên ý nghĩa, "
        f"mỗi cách một dòng, KHÔNG đánh số, KHÔNG giải thích:\n{question}"
        if lang == "vi"
        else f"Rewrite the following question in {n} different ways with the same meaning, "
        f"one per line, NO numbering, NO explanation:\n{question}"
    )
    raw = _call_llm_once(prompt, model, api_key, max_tokens=120)
    if not raw:
        return []
    variants = [
        line.strip().lstrip("-•*0123456789. ").strip()
        for line in raw.splitlines()
        if line.strip()
    ]
    variants = [v for v in variants if v and v.lower() != question.strip().lower()]
    return variants[:n]


def _llm_filter_chunks(
    question: str,
    chunks: list[dict],
    ollama_model: str,
    api_key: str | None,
    groq_model: str | None,
) -> list[dict] | None:
    """Ask the LLM which chunks are genuinely relevant.
    Returns None on error (caller should fall back to all chunks).
    Returns [] when LLM explicitly says none are relevant.
    """
    if not chunks:
        return chunks

    numbered = "\n\n".join(f"[{i+1}] {c['content'][:300]}" for i, c in enumerate(chunks))
    prompt = f"{_FILTER_SYSTEM}\n\nQuestion: {question}\n\nExcerpts:\n{numbered}\n\nRelevant numbers:"

    raw = ""
    try:
        if api_key:
            raw = _call_llm_once(prompt, groq_model, api_key, max_tokens=50)
        if not raw:
            resp = httpx.post(
                f"{_OLLAMA_URL}/api/generate",
                json={"model": ollama_model, "prompt": prompt, "stream": False, "options": {"num_predict": 50}},
                timeout=httpx.Timeout(connect=10.0, read=30.0, write=5.0, pool=5.0),
            )
            if resp.status_code == 200:
                raw = resp.json().get("response", "").strip()
    except Exception:
        return None  # error → caller falls back to all chunks

    if raw.lower().strip() == "none":
        return []  # explicit "none relevant" — do not fall back
    if not raw:
        return None  # API/network failure (e.g. rate limit) — fall back to all chunks,
        # NOT the same as the LLM explicitly saying nothing is relevant

    kept = []
    for part in re.split(r"[,\s]+", raw):
        part = part.strip().rstrip(".")
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < len(chunks):
                kept.append(chunks[idx])

    return kept if kept else None  # empty parse → treat as error, fall back


_CEREBRAS_MODEL_IDS = {"gpt-oss-120b", "gemma-4-31b", "zai-glm-4.7", "llama-3.3-70b", "llama3.1-70b", "llama3.1-8b"}


def _resolve_env_key(model: str) -> str:
    """Pick the right env API key based on the model name when no key was supplied by the client."""
    m = model.lower()
    if "gemini" in m:
        return os.environ.get("GEMINI_API_KEY", "")
    if "claude" in m:
        return os.environ.get("ANTHROPIC_API_KEY", "")
    if model in _CEREBRAS_MODEL_IDS:
        return os.environ.get("CEREBRAS_API_KEY", "")
    if any(p in m for p in ("gpt-", "o1-", "o3-", "o4-")):
        return os.environ.get("OPENAI_API_KEY", "")
    if "/" in m:
        return os.environ.get("OPENROUTER_API_KEY", "")
    return os.environ.get("GROQ_API_KEY", "")


def _stream_llm(
    prompt: str,
    ollama_model: str,
    api_key: str | None,
    groq_model: str | None,
    fallback_vi: str | None = None,
    fallback_en: str | None = None,
) -> Generator[str, None, None]:
    """Stream a prompt through Cloud API (Groq, OpenAI, Gemini, OpenRouter, Cerebras) or Ollama."""
    model_str = str(groq_model or "").strip()
    resolved_key = str(api_key).strip() if api_key else _resolve_env_key(model_str)
    if resolved_key:
        api_key_str = resolved_key
        model_lower = model_str.lower()

        # Route by API key prefix first — most reliable signal
        # 1. Groq (gsk_ prefix — must come before "/" check since Groq has models with "/" in ID)
        if api_key_str.startswith("gsk_"):
            yield from _stream_openai_compatible(
                prompt,
                model_str or "llama-3.3-70b-versatile",
                api_key_str,
                "https://api.groq.com/openai/v1"
            )
            return

        # 2. Cerebras
        if api_key_str.startswith("csk-"):
            yield from _stream_openai_compatible(
                prompt,
                model_str or "llama-3.3-70b",
                api_key_str,
                "https://api.cerebras.ai/v1"
            )
            return

        # 3. OpenRouter
        if api_key_str.startswith("sk-or-") or "/" in model_lower:
            yield from _stream_openai_compatible(
                prompt,
                model_str or "meta-llama/llama-3.3-70b-instruct:free",
                api_key_str,
                "https://openrouter.ai/api/v1"
            )
            return

        # 4. Gemini
        if "gemini" in model_lower or api_key_str.startswith("AIzaSy"):
            yield from _stream_gemini_native(
                prompt,
                model_str or "gemini-2.0-flash",
                api_key_str
            )
            return

        # 5. Anthropic (sk-ant- prefix — must come before generic OpenAI "sk-" check)
        if "claude" in model_lower or api_key_str.startswith("sk-ant-"):
            yield from _stream_anthropic_native(
                prompt,
                model_str or "claude-sonnet-5",
                api_key_str
            )
            return

        # 6. OpenAI
        if "gpt-" in model_lower or "o1-" in model_lower or api_key_str.startswith("sk-proj-") or api_key_str.startswith("sk-"):
            yield from _stream_openai_compatible(
                prompt,
                model_str or "gpt-4o-mini",
                api_key_str,
                "https://api.openai.com/v1"
            )
            return

        # 7. Groq fallback by model name (no key prefix match above)
        if "llama" in model_lower or "gemma2" in model_lower or "qwen" in model_lower:
            yield from _stream_openai_compatible(
                prompt,
                model_str or "llama-3.3-70b-versatile",
                api_key_str,
                "https://api.groq.com/openai/v1"
            )
            return

    try:
        with httpx.stream(
            "POST",
            f"{_OLLAMA_URL}/api/generate",
            json={"model": ollama_model, "prompt": prompt, "stream": True},
            timeout=httpx.Timeout(connect=15.0, read=120.0, write=10.0, pool=10.0),
        ) as response:
            for line in response.iter_lines():
                if not line:
                    continue
                data = json.loads(line)
                if "error" in data:
                    break
                token = data.get("response", "")
                if token:
                    yield _sse({"type": "token", "token": token})
                if data.get("done"):
                    return
    except (httpx.ReadTimeout, httpx.ConnectError, httpx.RemoteProtocolError) as e:
        logger.warning("Ollama stream %s: %s", type(e).__name__, e)
    except Exception as e:
        logger.warning("Ollama stream unexpected error: %s", e)
    # Fallback when LLM is unreachable
    fb = fallback_vi or "Hiện tại tôi không thể kết nối model. Vui lòng thử lại hoặc cấu hình API key."
    yield from _stream_text_gradually(fb, delay=0.018)


def _stream_gemini_native(prompt: str, model: str, api_key: str) -> Generator[str, None, None]:
    model_clean = model.replace("models/", "")
    is_25 = "2.5" in model_clean
    api_ver = "v1beta" if is_25 or any(x in model_clean for x in ["preview", "exp", "latest"]) else "v1"
    url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{model_clean}:streamGenerateContent?alt=sse&key={api_key}"
    headers = {"Content-Type": "application/json"}
    gen_cfg: dict = {"maxOutputTokens": 4096}
    if is_25:
        gen_cfg["thinkingConfig"] = {"thinkingBudget": 0}
    json_data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": gen_cfg,
    }
    token_count = 0
    try:
        with httpx.stream(
            "POST",
            url,
            headers=headers,
            json=json_data,
            timeout=httpx.Timeout(connect=15.0, read=180.0, write=10.0, pool=10.0),
        ) as resp:
            if resp.status_code != 200:
                resp.read()
                try:
                    err = resp.json()
                    msg = err.get("error", {}).get("message", resp.text)
                except Exception:
                    msg = resp.text
                logger.warning("Gemini %s error %s: %s", model_clean, resp.status_code, msg[:300])
                yield _sse({"type": "token", "token": f"Lỗi Gemini API ({resp.status_code}): {msg}"})
                return
            for line in resp.iter_lines():
                if not line:
                    continue
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        candidates = data.get("candidates") or []
                        if not candidates:
                            continue
                        parts = candidates[0].get("content", {}).get("parts", [])
                        token = "".join(p.get("text", "") for p in parts if not p.get("thought", False))
                        if token:
                            token_count += 1
                            yield _sse({"type": "token", "token": token})
                    except Exception:
                        pass
    except Exception as e:
        logger.warning("Gemini stream error: %s", e)
        yield _sse({"type": "token", "token": f"Lỗi kết nối Gemini API: {e}"})
        return
    if token_count == 0:
        logger.warning("Gemini %s returned no tokens", model_clean)
        yield _sse({"type": "token", "token": f"⚠️ Gemini **{model_clean}** không phản hồi. Kiểm tra API key hoặc thử lại."})


def _stream_anthropic_native(prompt: str, model: str, api_key: str) -> Generator[str, None, None]:
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    json_data = {
        "model": model,
        "max_tokens": 4096,
        "stream": True,
        "messages": [{"role": "user", "content": prompt}],
    }
    token_count = 0
    try:
        with httpx.stream(
            "POST",
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=json_data,
            timeout=httpx.Timeout(connect=15.0, read=180.0, write=10.0, pool=10.0),
        ) as resp:
            if resp.status_code != 200:
                resp.read()
                try:
                    err = resp.json()
                    msg = err.get("error", {}).get("message", resp.text)
                except Exception:
                    msg = resp.text
                logger.warning("Anthropic %s error %s: %s", model, resp.status_code, msg[:300])
                yield _sse({"type": "token", "token": f"Lỗi Anthropic API ({resp.status_code}): {msg}"})
                return
            event_type = None
            for line in resp.iter_lines():
                if not line:
                    continue
                if line.startswith("event: "):
                    event_type = line[7:].strip()
                    continue
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                    except Exception:
                        continue
                    if event_type == "content_block_delta":
                        token = data.get("delta", {}).get("text") or ""
                        if token:
                            token_count += 1
                            yield _sse({"type": "token", "token": token})
    except Exception as e:
        logger.warning("Anthropic stream error: %s", e)
        yield _sse({"type": "token", "token": f"Lỗi kết nối Anthropic API: {e}"})
        return
    if token_count == 0:
        logger.warning("Anthropic %s returned no tokens", model)
        yield _sse({"type": "token", "token": f"⚠️ Model **{model}** không phản hồi. Kiểm tra API key hoặc thử lại."})


def _stream_openai_compatible(prompt: str, model: str, api_key: str, base_url: str) -> Generator[str, None, None]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    if "openrouter.ai" in base_url:
        headers["HTTP-Referer"] = "https://github.com/aansensei/chatRAG"
        headers["X-Title"] = "chatRAG"
        
    json_data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
        "max_tokens": 2048,
    }
    
    token_count = 0
    try:
        with httpx.stream(
            "POST",
            f"{base_url}/chat/completions",
            headers=headers,
            json=json_data,
            timeout=httpx.Timeout(connect=15.0, read=180.0, write=10.0, pool=10.0),
        ) as resp:
            if resp.status_code != 200:
                resp.read()
                try:
                    err = resp.json()
                    msg = err.get("error", {}).get("message", resp.text)
                except Exception:
                    msg = resp.text
                logger.warning("API %s error %s: %s", base_url, resp.status_code, msg[:300])
                yield _sse({"type": "token", "token": f"Lỗi API ({resp.status_code}): {msg}"})
                return
            for line in resp.iter_lines():
                if not line or line == "data: [DONE]":
                    continue
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        choices = data.get("choices") or []
                        if not choices:
                            continue
                        delta = choices[0].get("delta", {})
                        token = delta.get("content") or ""
                        if token:
                            token_count += 1
                            yield _sse({"type": "token", "token": token})
                    except Exception:
                        pass
    except Exception as e:
        logger.warning("API stream error (%s): %s", base_url, e)
        yield _sse({"type": "token", "token": f"Lỗi kết nối API: {e}"})
        return
    if token_count == 0:
        logger.warning("API stream (%s) returned no tokens for model %s", base_url, model)
        yield _sse({"type": "token", "token": f"⚠️ Model **{model}** không phản hồi. Thử đổi sang model khác (Gemini Flash, Llama 3.3...)."})


_MAX_HISTORY_TURNS = 4
_MAX_HISTORY_CHARS = 15000


def _format_history(history: list[dict] | None) -> str:
    if not history:
        return ""
    msgs = history[-(_MAX_HISTORY_TURNS * 2):]
    lines = []
    total = 0
    for m in msgs:
        role = "Người dùng" if m.get("role") == "user" else "Ciel"
        content = (m.get("content") or "").strip()
        if not content:
            continue
        if len(content) > 4000:
            content = content[:4000] + "…"
        line = f"{role}: {content}"
        total += len(line)
        if total > _MAX_HISTORY_CHARS:
            break
        lines.append(line)
    if not lines:
        return ""
    return "Lịch sử hội thoại gần đây:\n" + "\n".join(lines) + "\n\n"


_REWRITE_TRIGGERS_VI = (
    "đề bài", "điều đó", "nó", "cái đó", "phần đó", "vấn đề đó",
    "file đó", "tài liệu đó", "câu hỏi đó", "y đó", "kết quả đó",
    "ở trên", "như vậy", "theo đó", "liên quan", "điều này", "việc này",
)
_REWRITE_TRIGGERS_EN = (
    "it", "that", "those", "this", "the above", "said document",
    "the file", "the question", "the result", "as mentioned",
)


def _should_rewrite(question: str, history: list[dict] | None) -> bool:
    """Return True when the question is likely a follow-up that needs context to be understood.

    Only triggers when the question contains an explicit anaphor (it/that/this/đó/này...).
    Previously this triggered for any short query, which caused unrelated questions to inherit
    semantics from previous Q&A and pull wrong chunks.
    """
    if not history:
        return False
    q = question.strip().lower()
    if len(q) > 120:
        return False
    if any(t in q for t in _REWRITE_TRIGGERS_VI):
        return True
    if any(t in q for t in _REWRITE_TRIGGERS_EN):
        return True
    return False


def _augment_for_embedding(question: str, history: list[dict] | None) -> str:
    """Prepend the previous user question for short follow-ups — no LLM needed.

    "đề bài hỏi gì?" alone has poor embedding. With context:
    "câu hỏi tour du lịch 5 sao → đề bài hỏi gì?" works much better.
    Only triggers when query is short (<= 12 words) and history exists.
    """
    if not history or len(question.split()) > 12:
        return question
    for msg in reversed(history):
        if msg.get("role") == "user":
            prev = msg.get("content", "").strip()
            if prev and prev != question and len(prev) > 5:
                return f"{prev} {question}"
    return question


def _rewrite_query_with_history(
    question: str,
    history: list[dict] | None,
    ollama_model: str,
    api_key: str | None,
) -> str:
    """Rewrite a follow-up question into a standalone query using recent history.

    Returns the rewritten query, or the original question if rewriting fails.
    """
    if not _should_rewrite(question, history):
        return question

    history_text = _format_history(history)
    if not history_text:
        return question

    prompt = (
        f"{history_text}"
        f"Câu hỏi hiện tại: {question}\n"
        "Viết lại câu hỏi trên thành câu standalone đầy đủ, tự nó hiểu được mà không cần lịch sử. "
        "Chỉ trả về câu mới, không giải thích. Tối đa 80 ký tự."
    )

    raw = ""
    try:
        if api_key:
            raw = _call_llm_once(prompt, ollama_model, api_key, max_tokens=80)
        if not raw:
            resp = httpx.post(
                f"{_OLLAMA_URL}/api/generate",
                json={
                    "model": ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": 80, "temperature": 0.0},
                },
                timeout=httpx.Timeout(connect=8.0, read=15.0, write=4.0, pool=4.0),
            )
            if resp.status_code == 200:
                raw = resp.json().get("response", "").strip()
    except Exception:
        return question

    rewritten = raw.strip().strip('"').strip("'")
    if rewritten and 5 < len(rewritten) <= 200:
        return rewritten
    return question



def stream_ask(
    question: str,
    collections: list[str] | None = None,
    hybrid: bool = False,
    model: str | None = None,
    api_key: str | None = None,
    history: list[dict] | None = None,
    chat_notes: str = "",
) -> Generator[str, None, None]:
    ollama_model = model or _OLLAMA_MODEL

    # Strip web search prefix early — before memory extraction and fast-paths
    # so they only see the real question, not injected web content
    web_extra_context = ""
    web_search_query = ""
    _ws_match = _WEB_SEARCH_PREFIX.match(question)
    if _ws_match:
        web_search_query = _ws_match.group(1).strip()
        web_extra_context = _ws_match.group(2).strip()
        question = _ws_match.group(3).strip()

    lang = _detect_lang(question)
    history_block = _format_history(history)

    _facts = _auto_extract_memory(question)
    _is_instruction_type = bool(_facts and (
        bool(_INSTRUCTION_TRIGGER.search(question)) or
        (bool(_PREFERENCE_SIGNAL.search(question)) and bool(_SOFT_ENDING.search(question)))
    ))
    _new_memories: list[str] = []
    for _fact in _facts:
        saved = add_memory_internal(_fact)
        if saved:
            _new_memories.append(_fact)
    memory_block = _format_memory_block()
    chat_note_block = (
        f"[Ghi chú cho cuộc trò chuyện này — ưu tiên cao]\n{chat_notes.strip()}\n\n"
        if chat_notes and chat_notes.strip() else ""
    )
    for _mem in _new_memories:
        yield _sse({"type": "memory_saved", "content": _mem})

    # Instruction / teaching message — skip RAG entirely, confirm immediately
    if _is_instruction_type:
        ack = (
            "Đã ghi nhớ! Tôi sẽ áp dụng điều này cho các cuộc trò chuyện tiếp theo."
            if lang == "vi"
            else "Got it! I'll keep this in mind going forward."
        )
        yield from _stream_text_gradually(ack)
        yield _sse({"type": "done", "sources": [], "confidence": 1.0})
        return

    # Date/time query — answer instantly from system clock, no RAG needed
    if _DATETIME_PAT.search(question) and len(question) < 120:
        answer = _get_vn_datetime_answer(lang)
        yield from _stream_text_gradually(answer)
        yield _sse({"type": "done", "sources": [], "confidence": 1.0})
        return

    confidence_val = None

    # Wake-up: "ciel ơi" / "シエルさん" — random greeting, no LLM needed.
    if _is_wakeup_query(question):
        if lang == "ja":
            greeting = random.choice(_GREETINGS_JP)
        elif lang == "vi":
            greeting = random.choice(_GREETINGS_VI)
        else:
            greeting = random.choice(_GREETINGS_EN)
        yield from _stream_text_gradually(greeting, delay=0.022)
        yield _sse({"type": "done", "sources": [], "confidence": confidence_val})
        return

    # Memory listing — directly return stored memories instead of doing RAG.
    if _is_memory_list_query(question):
        mem_items = get_memories()
        if not mem_items:
            msg = (
                "Hiện tôi chưa lưu ghi nhớ nào về bạn. Bạn có thể thêm trong avatar → Memory."
                if lang == "vi"
                else "I don't have any memories saved about you yet. Add some via the avatar → Memory."
            )
            yield from _stream_text_gradually(msg)
        else:
            header = "Đây là những gì tôi nhớ về bạn:" if lang == "vi" else "Here's what I remember about you:"
            body = "\n".join(f"- {m.get('content', '').strip()}" for m in mem_items if m.get("content"))
            yield from _stream_text_gradually(f"{header}\n\n{body}")
        yield _sse({"type": "done", "sources": [], "confidence": confidence_val})
        return

    # Identity / capability questions — LLM with strong Ciel persona.
    if _is_identity_query(question):
        if lang == "ja":
            system = (
                f"{_CIEL_IDENTITY}"
                "あなたはchatRAGの社内AIアシスタント、Cielです。"
                "ユーザーはあなた自身について質問しています。"
                "自然に、友好的に、簡潔に答えてください。日本語で答えること。"
            )
        elif lang == "vi":
            system = _IDENTITY_SYSTEM_VI
        else:
            system = _IDENTITY_SYSTEM_EN
        prompt_identity = f"{system}\n\n{memory_block}{history_block}{chat_note_block}Question: {question}\nCiel:"
        yield from _stream_llm(prompt_identity, ollama_model, api_key, model)
        yield _sse({"type": "done", "sources": [], "confidence": confidence_val})
        return

    # RAG explanation — LLM for natural response.
    if _is_rag_query(question):
        system = _RAG_SYSTEM_VI if lang == "vi" else _RAG_SYSTEM_EN
        prompt_rag = f"{system}\n\n{memory_block}{history_block}{chat_note_block}Question: {question}\nCiel:"
        yield from _stream_llm(prompt_rag, ollama_model, api_key, model)
        yield _sse({"type": "done", "sources": [], "confidence": confidence_val})
        return

    # Calculate fast-path — safe AST eval, no RAG needed.
    pct_match = _PERCENT_OF_RE.search(question)
    calc_match = _CALC_TRIGGER.match(question.strip())
    if pct_match:
        pct = float(pct_match.group(1).replace(",", ""))
        base = float(pct_match.group(2).replace(",", ""))
        result = pct / 100 * base
        label = f"{pct_match.group(1)}% of {pct_match.group(2)}"
        yield from _stream_text_gradually(f"**{label} = {_fmt_num(result)}**")
        yield _sse({"type": "done", "sources": [], "confidence": 1.0})
        return
    if calc_match:
        expr_str = calc_match.group(1).strip()
        result = _safe_eval(expr_str)
        if result is not None:
            yield from _stream_text_gradually(f"**{expr_str} = {_fmt_num(result)}**")
            yield _sse({"type": "done", "sources": [], "confidence": 1.0})
            return

    # Web browse fast-path — frontend injected page content, skip vector search.
    web_match = _WEB_BROWSE_PREFIX.match(question)
    if web_match:
        web_url = web_match.group(1).strip()
        web_content = web_match.group(2).strip()
        real_question = web_match.group(3).strip()
        web_system = (
            f"{_CIEL_IDENTITY}"
            "Người dùng đã cung cấp nội dung trang web. Trả lời câu hỏi DỰA TRÊN NỘI DUNG ĐÓ. "
            "Nếu nội dung không đủ, nói rõ. KHÔNG bịa thêm. Ngắn gọn. Tiếng Việt."
            if lang == "vi"
            else "The user provided web page content. Answer the question BASED ON THAT CONTENT. "
                 "If content is insufficient, say so. Do NOT fabricate. Be concise."
        )
        web_prompt = (
            f"{web_system}\n\n{memory_block}{history_block}"
            f"Nội dung trang {web_url}:\n{web_content}\n\n"
            f"Câu hỏi: {real_question}\nCiel:"
        )
        yield _sse({"type": "step", "step": "generating"})
        yield from _stream_llm(web_prompt, ollama_model, api_key, model)
        yield _sse({"type": "done", "sources": [{"id": 1, "content": web_content[:200], "filename": web_url, "similarity": 1.0}], "confidence": 1.0})
        return

    try:
        yield _sse({"type": "step", "step": "embedding"})
        search_query = _rewrite_query_with_history(question, history, ollama_model, api_key)
        embed_query = _augment_for_embedding(search_query, history)
        vector = embed_text(embed_query)

        # HyDE: generate a hypothetical answer and blend its embedding with the query vector.
        # Significantly improves recall for short or vague queries at the cost of one fast LLM call.
        _hyde_key = api_key or _resolve_env_key(str(model or ""))
        if _hyde_key and len(search_query.strip()) < 150:
            _hyde_vec = _hyde_query_vector(search_query, lang, model, _hyde_key)
            if _hyde_vec and len(_hyde_vec) == len(vector):
                vector = [(_a + _b) / 2 for _a, _b in zip(vector, _hyde_vec)]

        yield _sse({"type": "step", "step": "searching"})
        try:
            # No folder explicitly selected in the UI ("All folders") — if the question
            # names a real folder/collection, scope to it. See _detect_collections_from_query.
            if not collections:
                _detected_collections = _detect_collections_from_query(question)
                if _detected_collections:
                    collections = _detected_collections

            # Filename-first: if query looks like "summarize <filename>", fetch that doc directly.
            fn_tokens, fn_strong = _extract_filename_tokens(question)
            filename_chunks: list[dict] = []
            filename_doc_ids: set = set()
            if fn_tokens:
                filename_chunks = filename_search_chunks(fn_tokens, collections=collections or None)
                filename_doc_ids = {c.get("document_id") for c in filename_chunks if c.get("document_id")}

            # Vector search — if filename match found, exclude those docs to avoid duplicate context
            chunks = search_chunks(vector, match_count=_TOP_K, threshold=0.1, collections=collections or None)

            # Filename match: use only those chunks — no vector supplement from unrelated docs.
            if filename_doc_ids:
                chunks = filename_chunks
            else:
                # Supplementary searches (accent-stripped question, LLM-paraphrased
                # multi-query variants) used to run one-after-another, adding real
                # wall-clock latency before the answer could start streaming. They're
                # independent of each other, so run them concurrently instead.
                def _search_text(q: str) -> list[dict]:
                    try:
                        vec = embed_text(q)
                        return search_chunks(vec, match_count=_TOP_K, threshold=0.1, collections=collections or None)
                    except Exception as exc:
                        logger.warning("supplementary search failed for %r: %s", q, exc)
                        return []

                stripped_question = _strip_accents(question)
                needs_stripped = stripped_question != question
                needs_multi_query = bool(_hyde_key) and len(question.strip()) >= 15
                seen_ids = {c.get("id") for c in chunks if c.get("id")}

                if needs_stripped or needs_multi_query:
                    with ThreadPoolExecutor(max_workers=3) as ex:
                        stripped_future = ex.submit(_search_text, stripped_question) if needs_stripped else None
                        variants_future = (
                            ex.submit(_generate_query_variants, question, lang, model, _hyde_key)
                            if needs_multi_query else None
                        )

                        if stripped_future:
                            for c in stripped_future.result():
                                c_id = c.get("id")
                                if c_id and c_id not in seen_ids:
                                    chunks.append(c)
                                    seen_ids.add(c_id)

                        if variants_future:
                            variants = variants_future.result() or []
                            if variants:
                                variant_search_futures = [ex.submit(_search_text, v) for v in variants]
                                for vf in variant_search_futures:
                                    for c in vf.result():
                                        c_id = c.get("id")
                                        if c_id and c_id not in seen_ids:
                                            chunks.append(c)
                                            seen_ids.add(c_id)

            kw_tokens = _KEYWORD_RE.findall(question)
            kw_tokens += [w for w in re.findall(r'\w+', question) if len(w) >= 4]
            q_lower = question.lower()
            for vi_term, abbr in _VI_ABBR.items():
                if vi_term in q_lower:
                    kw_tokens.append(abbr)
            stripped_q = _strip_accents(question)
            if stripped_q != question:
                kw_tokens += [w for w in re.findall(r'\w+', stripped_q) if len(w) >= 4]
            kw_tokens = list(dict.fromkeys(kw_tokens))
            if kw_tokens and not filename_doc_ids:
                seen_ids = {c.get("id") for c in chunks if c.get("id")}
                for kw_chunk in keyword_search_chunks(kw_tokens[:6], collections=collections or None):
                    if kw_chunk.get("id") not in seen_ids:
                        chunks.append(kw_chunk)
                        seen_ids.add(kw_chunk.get("id"))

            # Fuse vector-similarity ranking with a BM25 keyword ranking via
            # reciprocal rank fusion — vector search alone under-ranks exact
            # matches (names, codes, numbers) that BM25 catches, and keyword
            # search alone has no semantic signal. RRF combines both rankings
            # without needing comparable score scales.
            if not filename_doc_ids and chunks:
                vector_rank_ids = [
                    c["id"] for c in sorted(chunks, key=lambda x: x.get("similarity", 0.0), reverse=True)
                    if c.get("id")
                ]
                bm25_rank_ids = _bm25_rank(kw_tokens or _TOKEN_RE.findall(question.lower()), chunks)
                fused = _reciprocal_rank_fusion([vector_rank_ids, bm25_rank_ids])
                chunks.sort(key=lambda x: fused.get(x.get("id"), 0.0), reverse=True)
            else:
                # Filename hits first, then by similarity.
                chunks.sort(key=lambda x: (x.get("document_id") in filename_doc_ids, x.get("similarity", 0.0)), reverse=True)
            chunks = chunks[: _TOP_K * 2]

            # If STRONG filename tokens were extracted but NO matching document was found,
            # always tell the user explicitly — even in hybrid mode, making up info about a
            # non-existent document is worse than a clear "not found" message.
            if fn_strong and not filename_doc_ids:
                token_hint = fn_tokens[0] if fn_tokens else ""
                msg = (
                    f"Không tìm thấy tài liệu nào có tên gần giống **{token_hint}** trong kho. "
                    "Hãy kiểm tra lại tên file hoặc upload tài liệu trước."
                    if lang == "vi"
                    else f"No document matching **{token_hint}** was found in the knowledge base. "
                         "Please check the filename or upload the document first."
                )
                yield _sse({"type": "done", "answer": msg, "sources": []})
                return
        except Exception:
            chunks = []

        has_prior_context = any(h.get("role") == "assistant" for h in (history or []))

        if not chunks and not hybrid and not has_prior_context and not web_extra_context:
            msg = (
                "Không tìm thấy thông tin liên quan trong tài liệu."
                if lang == "vi"
                else "No relevant information found in the documents."
            )
            yield _sse({"type": "done", "answer": msg, "sources": [], "confidence": confidence_val})
            return

        if chunks:
            has_tabular = any("  |  " in (c.get("content") or "") for c in chunks[:5])
            has_faq_intent = bool(re.search(
                r"câu hỏi thường gặp|hỏi[\s-]*đáp|\bfaq\b|frequently asked questions|q\s*&\s*a",
                question, re.IGNORECASE,
            ))
            if filename_doc_ids or has_tabular:
                filtered = chunks
            elif _RERANKER_ENABLED and _bge_rerank is not None and not web_extra_context:
                yield _sse({"type": "step", "step": "filtering"})
                try:
                    filtered = _bge_rerank(question, chunks, top_n=_TOP_K)
                    if not filtered:
                        filtered = chunks
                    else:
                        top_score = filtered[0].get("similarity")
                        if isinstance(top_score, (int, float)):
                            import math
                            confidence_val = round(1.0 / (1.0 + math.exp(-float(top_score))), 2)
                except Exception:
                    filtered = chunks
            else:
                yield _sse({"type": "step", "step": "filtering"})
                groq_filter_model = model if (api_key and api_key.startswith("gsk_")) else None
                filter_result = _llm_filter_chunks(question, chunks, ollama_model, api_key, groq_filter_model)
                if filter_result is None:
                    filtered = chunks  # error → use all chunks
                elif not filter_result:
                    # LLM explicitly said nothing is relevant — don't fall back
                    if not has_prior_context and not web_extra_context:
                        msg = (
                            "Không tìm thấy thông tin liên quan trong tài liệu."
                            if lang == "vi"
                            else "No relevant information found in the documents."
                        )
                        yield _sse({"type": "done", "sources": [], "confidence": confidence_val})
                        return
                    filtered = []
                else:
                    filtered = filter_result

            # Build sources from filtered chunks (post-filter, so only relevant docs appear)
            sources = []
            _seen_doc_ids_f: set[str] = set()
            for c in filtered:
                doc_id = c.get("document_id", "")
                if doc_id and doc_id in _seen_doc_ids_f:
                    continue
                if doc_id:
                    _seen_doc_ids_f.add(doc_id)
                meta = c.get("metadata") or {}
                raw_src = meta.get("source", "") if isinstance(meta, dict) else ""
                filename = raw_src.split("\\")[-1].split("/")[-1] if raw_src else f"Source {len(sources)+1}"
                section = (c.get("section_title") or "").strip()
                if section.upper() in _GENERIC_SECTION_TITLES:
                    section = ""
                sources.append({
                    "id": len(sources) + 1,
                    "content": c["content"][:200],
                    "section": section or None,
                    "similarity": round(c["similarity"], 3),
                    "filename": filename,
                    "document_id": doc_id,
                })

            # Yield sources AFTER filtering so only relevant docs are shown
            yield _sse({"type": "sources", "sources": sources})

            # Parent-child context expansion: expand each matched chunk with neighboring
            # chunks from the same document, giving the LLM more context to answer from.
            # Skip for filename/tabular queries — those already have full doc context.
            if not filename_doc_ids and not has_tabular:
                try:
                    filtered = fetch_context_windows(filtered, window=1)
                except Exception as e:
                    logger.warning("fetch_context_windows failed: %s", e)

            parts = []
            for i, c in enumerate(filtered):
                section = c.get("section_title") or ""
                header = f"[{i+1}]" + (f" [{section}]" if section else "")
                parts.append(f"{header}\n{c['content'][:_MAX_CHUNK_CHARS * 2]}")
            context = "\n\n".join(parts)

            if has_faq_intent:
                system = (
                    "Người dùng muốn một danh sách CÂU HỎI THƯỜNG GẶP (FAQ) rút ra từ tài liệu, "
                    "KHÔNG phải một bài tóm tắt văn xuôi liên tục. "
                    "Tự đặt ra 4-8 câu hỏi mà người đọc tài liệu này thường thắc mắc, dựa trên các luận điểm/số liệu chính, "
                    "rồi trả lời từng câu bằng nội dung trong tài liệu. Định dạng mỗi mục: "
                    "'**Q: <câu hỏi>**' xuống dòng '<câu trả lời ngắn gọn, có trích dẫn [N] nếu có>'. "
                    "TUYỆT ĐỐI KHÔNG viết 'Tôi là', 'Xin chào', hay câu giới thiệu. KHÔNG dùng emoji. Tiếng Việt."
                    if lang == "vi"
                    else "The user wants a list of FREQUENTLY ASKED QUESTIONS (FAQ) drawn from the document, "
                    "NOT a continuous prose summary. "
                    "Come up with 4-8 questions a reader of this document would likely ask, based on its key "
                    "points/data, then answer each from the document content. Format each entry as "
                    "'**Q: <question>**' on its own line, followed by '<concise answer, with [N] citation if available>'. "
                    "ABSOLUTELY DO NOT write 'I am', 'Hello', or any self-introduction. No emojis."
                )
            elif filename_doc_ids or has_tabular:
                system = (
                    "Bắt đầu ngay vào nội dung tóm tắt hoặc câu trả lời. "
                    "TUYỆT ĐỐI KHÔNG viết 'Tôi là', 'Xin chào', hay bất kỳ câu giới thiệu nào. "
                    "KHÔNG dùng emoji. KHÔNG nói 'không có thông tin'. "
                    "Nội dung tài liệu đã được cung cấp bên dưới — đọc và tóm tắt trực tiếp. "
                    "Nếu có bảng số liệu, trích xuất rõ ràng. Ngắn gọn. Tiếng Việt."
                    if lang == "vi"
                    else "Start directly with the summary or answer. "
                    "ABSOLUTELY DO NOT write 'I am', 'Hello', or any self-introduction. "
                    "No emojis. Do not say 'no information'. "
                    "The document content is provided below — read and summarize it directly. "
                    "If tabular, extract numbers clearly. Be concise."
                )
            else:
                system = _SYSTEM_VI if lang == "vi" else _SYSTEM_EN
            web_supplement = (
                f"\n\nNguồn bổ sung từ web ('{web_search_query}'):\n{web_extra_context}"
                if web_extra_context else ""
            )
            prompt = f"{system}\n\n{memory_block}{history_block}Context:\n{context}{web_supplement}\n\n{chat_note_block}Question: {question}\nAnswer:"
        elif not chunks and has_prior_context:
            continuation_system = (
                f"{_CIEL_IDENTITY}"
                "Câu hỏi này là tiếp nối cuộc hội thoại trước. "
                "Dựa vào lịch sử hội thoại để trả lời — có thể tính toán, so sánh, hoặc tổng hợp từ các câu trả lời trước. "
                "KHÔNG bịa đặt thông tin không có trong hội thoại. Ngắn gọn. Tiếng Việt."
                if lang == "vi"
                else f"{_CIEL_IDENTITY}"
                     "This question continues the prior conversation. "
                     "Use conversation history to answer — you may calculate, compare, or summarize from prior answers. "
                     "Do NOT fabricate information not present in the conversation. Be concise."
            )
            prompt = f"{continuation_system}\n\n{memory_block}{history_block}{chat_note_block}Question: {question}\nAnswer:"
        else:
            if web_extra_context:
                web_only_system = (
                    f"{_CIEL_IDENTITY}"
                    "Kết quả tìm web đã được cung cấp bên dưới. "
                    "Hãy đọc kỹ và trả lời câu hỏi trực tiếp dựa trên nội dung đó. "
                    "TUYỆT ĐỐI KHÔNG nói 'không có tài liệu', 'không có thông tin nội bộ' hay câu tương tự — kết quả web ĐÃ CÓ SẴN. "
                    "Trả lời bằng Tiếng Việt, ngắn gọn, trực tiếp vào vấn đề."
                    if lang == "vi"
                    else f"{_CIEL_IDENTITY}"
                         "Web search results are provided below. Read them and answer the question directly. "
                         "Do NOT say 'no documents' or 'no information' — the web results ARE available. Be concise."
                )
                prompt = (
                    f"{web_only_system}\n\n{memory_block}{history_block}"
                    f"Kết quả tìm web cho '{web_search_query}':\n{web_extra_context}\n\n"
                    f"{chat_note_block}Question: {question}\nAnswer:"
                )
            else:
                hybrid_system = (
                    f"{_CIEL_IDENTITY}"
                    "Không tìm thấy tài liệu liên quan trong kho. Hãy trả lời dựa trên kiến thức chung của bạn. "
                    "Ghi chú ngắn rằng câu trả lời dựa trên kiến thức chung, không phải tài liệu nội bộ. "
                    "Ngắn gọn, tự nhiên. Tiếng Việt."
                    if lang == "vi"
                    else f"{_CIEL_IDENTITY}No relevant documents found. Answer using your general knowledge. "
                         "Briefly note the answer comes from general knowledge, not internal documents. Be concise."
                )
                prompt = f"{hybrid_system}\n\n{memory_block}{history_block}{chat_note_block}Question: {question}\nAnswer:"

        yield _sse({"type": "step", "step": "generating"})
        yield from _stream_llm(prompt, ollama_model, api_key, model)
        yield _sse({"type": "done", "sources": sources, "confidence": confidence_val})

    except Exception as exc:
        yield _sse({"type": "token", "token": f"Lỗi xử lý: {exc}"})
        yield _sse({"type": "done", "sources": [], "confidence": confidence_val})
