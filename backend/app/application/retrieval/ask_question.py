import json
import logging
import os
import random
import re
import time
import unicodedata
from typing import Generator

logger = logging.getLogger(__name__)

import httpx

from app.infrastructure.vector.supabase.repository import search_chunks, keyword_search_chunks, filename_search_chunks
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


_MEM_PATS_FULL = [
    re.compile(r"\b(?:tôi\s+tên|tên\s+(?:tôi|mình)\s+là|mình\s+tên|i'?m\s+called|my\s+name\s+is)\s+([^.,\n!?]{2,60})", re.IGNORECASE),
    re.compile(r"\b(?:tôi\s+là|mình\s+là|i\s+am\s+a|i'?m\s+a|i\s+work\s+as)\s+([^.,\n!?]{3,80})", re.IGNORECASE),
    re.compile(r"\b(?:tôi\s+(?:thích|ưa|ghét|không\s+thích)|i\s+prefer|i\s+like|i\s+hate)\s+([^.,\n!?]{3,100})", re.IGNORECASE),
    re.compile(r"\b(?:tôi\s+(?:làm|đang\s+làm\s+tại|sống\s+ở|ở)|i\s+work\s+at|i\s+live\s+in)\s+([^.,\n!?]{2,80})", re.IGNORECASE),
]

_MEM_PATS_CAPTURE = [
    re.compile(r"\b(?:hãy\s+nhớ\s+(?:là\s+|rằng\s+)?|nhớ\s+(?:giúp\s+(?:tôi\s+|mình\s+)?)?(?:là\s+|rằng\s+)?|remember\s+(?:that\s+)?|please\s+remember\s+)([^.\n!?]{5,200})", re.IGNORECASE),
]


def _auto_extract_memory(question: str) -> list[str]:
    """Extract facts user states about themselves. Returns list of memory strings to save."""
    if not question or len(question) < 6:
        return []
    extracted: list[str] = []

    for pat in _MEM_PATS_FULL:
        for m in pat.finditer(question):
            fact = m.group(0).strip().rstrip(".!?,")
            if "?" not in fact and len(fact) >= 4 and fact not in extracted:
                extracted.append(fact)

    for pat in _MEM_PATS_CAPTURE:
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
    "KHÔNG dùng emoji. "
)

_SYSTEM_EN = (
    "You are Ciel, the internal AI of chatRAG — NOT Qwen, Gemma, or Llama. "
    "Do NOT introduce yourself or state your name unless directly asked. No emojis. "
    "READ THE CONTEXT CAREFULLY BEFORE ANSWERING. "
    "Your answer must be grounded in the document context provided below. "
    "ALLOWED: synthesizing, translating, explaining, or calculating using information present in the context. "
    "FORBIDDEN: inventing names, project names, figures, or facts that are NOT in the context at all. "
    "If context contains partial information: cite what is present, state what is missing. "
    "Example: 'An Nguyen is mentioned in [1], but their specific title is not stated in the document.' "
    "If context has NO relevant information whatsoever: say 'The document does not contain this information.' "
    "Extract numbers and data from tables in the context when present. "
    "CITATION RULE: When you use information from chunk [N], append [N] at the end of that sentence. Example: 'Revenue reached $28M [2].' "
    "If the user asks multiple questions in one message, answer EACH one separately, numbered 1/ 2/ "
    "Respond in English. Be concise."
)

_SYSTEM_VI = (
    f"{_CIEL_IDENTITY}"
    "ĐỌC KỸ CONTEXT TRƯỚC KHI TRẢ LỜI. "
    "Câu trả lời phải dựa vào nội dung context bên dưới. "
    "ĐƯỢC PHÉP: tổng hợp, dịch thuật, giải thích, tính toán từ thông tin CÓ TRONG context. "
    "CẤM: bịa tên người, tên dự án, con số hoặc sự kiện KHÔNG có trong context. "
    "Nếu context có thông tin partial: trích thẳng những gì có và ghi rõ phần nào không được nêu. "
    "Ví dụ đúng: 'An Nguyễn được đề cập trong tài liệu [1], nhưng chức vụ cụ thể không được nêu.' "
    "Nếu context KHÔNG CÓ thông tin liên quan: nói 'Tài liệu không có thông tin về vấn đề này.' "
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
    "Nếu hỏi giới hạn: nói thật — chưa tạo được hình ảnh, chưa nhớ session, chưa duyệt web, chưa gửi email, chưa chạy code. "
    "Nếu hỏi tính năng cụ thể (ví dụ 'có tạo ảnh không'): trả lời thẳng có/không, giải thích ngắn. "
    "Trả lời bằng tiếng Việt."
)

_IDENTITY_SYSTEM_EN = (
    "Your name is Ciel, the internal AI assistant of chatRAG — NOT Qwen, Gemma, or any other model. "
    "The user is asking about you or your capabilities. "
    "Reply naturally and briefly — like a chat message. "
    "If asked your name: say 'I'm Ciel'. "
    "If asked capabilities: explain you help search and summarize internal documents via RAG. "
    "If asked limitations: be honest — you can't generate images, don't remember sessions, can't browse the web or send emails. "
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
• Hiểu tiếng Việt, tiếng Anh, tiếng Nhật và nhiều ngôn ngữ khác.
• Chạy local (Ollama) hoặc cloud nhanh (Groq).

**Tôi chưa làm được:**
• Tự học hay ghi nhớ cuộc hội thoại qua các session.
• Truy cập internet hoặc dữ liệu ngoài tài liệu đã tải lên.
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


def _intro_lang(question: str) -> str:
    """Vietnamese by default; English only when the query is clearly English."""
    if _detect_lang(question) == "vi":
        return "vi"
    q = _strip_vi(question).rstrip("?!. ").strip()
    return "en" if any(p in q for p in _IDENTITY_EN) else "vi"


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
                return r.json()["choices"][0]["message"]["content"].strip()
            return ""
        if key.startswith("csk-"):
            r = httpx.post("https://api.cerebras.ai/v1/chat/completions", headers=headers,
                           json={"model": mod or "llama-3.3-70b", "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens},
                           timeout=httpx.Timeout(connect=8.0, read=20.0, write=4.0, pool=4.0))
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
            logger.warning("Cerebras filter call %s: %s", r.status_code, r.text[:200])
            return ""
        if key.startswith("sk-or-") or (":free" in mod_lower and "/" in mod_lower):
            headers["HTTP-Referer"] = "https://github.com/aansensei/chatRAG"
            headers["X-Title"] = "chatRAG"
            r = httpx.post("https://openrouter.ai/api/v1/chat/completions", headers=headers,
                           json={"model": mod, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens}, timeout=t)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
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
        if "gpt-" in mod_lower or "o1-" in mod_lower or key.startswith("sk-proj-") or key.startswith("sk-"):
            r = httpx.post("https://api.openai.com/v1/chat/completions", headers=headers,
                           json={"model": mod or "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens}, timeout=t)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        logger.warning("_call_llm_once failed: %s", exc)
    return ""


def _llm_filter_chunks(
    question: str,
    chunks: list[dict],
    ollama_model: str,
    api_key: str | None,
    groq_model: str | None,
) -> list[dict]:
    """Ask the LLM which chunks are genuinely relevant. Falls back to all chunks on error."""
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
        return chunks

    if not raw or raw.lower().strip() == "none":
        return []

    kept = []
    for part in re.split(r"[,\s]+", raw):
        part = part.strip().rstrip(".")
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < len(chunks):
                kept.append(chunks[idx])

    return kept if kept else chunks


def _stream_llm(
    prompt: str,
    ollama_model: str,
    api_key: str | None,
    groq_model: str | None,
    fallback_vi: str | None = None,
    fallback_en: str | None = None,
) -> Generator[str, None, None]:
    """Stream a prompt through Cloud API (Groq, OpenAI, Gemini, OpenRouter, Cerebras) or Ollama."""
    if api_key:
        api_key_str = str(api_key).strip()
        model_str = str(groq_model or "").strip()
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
        if api_key_str.startswith("sk-or-") or ("/" in model_lower and ":free" in model_lower):
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

        # 5. OpenAI
        if "gpt-" in model_lower or "o1-" in model_lower or api_key_str.startswith("sk-proj-") or api_key_str.startswith("sk-"):
            yield from _stream_openai_compatible(
                prompt,
                model_str or "gpt-4o-mini",
                api_key_str,
                "https://api.openai.com/v1"
            )
            return

        # 6. Groq fallback by model name (no key prefix match above)
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
    except Exception:
        pass
    # Fallback when LLM is unreachable
    fb = fallback_vi or "Hiện tại tôi không thể kết nối model. Vui lòng thử lại hoặc cấu hình API key."
    yield from _stream_text_gradually(fb, delay=0.018)


def _stream_gemini_native(prompt: str, model: str, api_key: str) -> Generator[str, None, None]:
    model_clean = model.replace("models/", "")
    api_ver = "v1beta" if any(x in model_clean for x in ["2.5", "preview", "exp", "latest"]) else "v1"
    url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{model_clean}:streamGenerateContent?alt=sse&key={api_key}"
    headers = {"Content-Type": "application/json"}
    json_data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 2048},
    }
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
                        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                        token = "".join(p.get("text", "") for p in parts)
                        if token:
                            yield _sse({"type": "token", "token": token})
                    except Exception:
                        pass
    except Exception as e:
        logger.warning("Gemini stream error: %s", e)
        yield _sse({"type": "token", "token": f"Lỗi kết nối Gemini API: {e}"})


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
                        delta = data["choices"][0].get("delta", {})
                        token = delta.get("content") or ""
                        if token:
                            yield _sse({"type": "token", "token": token})
                    except Exception:
                        pass
    except Exception as e:
        logger.warning("API stream error (%s): %s", base_url, e)
        yield _sse({"type": "token", "token": f"Lỗi kết nối API: {e}"})


_MAX_HISTORY_TURNS = 4
_MAX_HISTORY_CHARS = 1500


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
        if len(content) > 400:
            content = content[:400] + "…"
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
) -> Generator[str, None, None]:
    ollama_model = model or _OLLAMA_MODEL
    lang = _detect_lang(question)
    history_block = _format_history(history)
    _new_memories: list[str] = []
    for _fact in _auto_extract_memory(question):
        saved = add_memory_internal(_fact)
        if saved:
            _new_memories.append(_fact)
    memory_block = _format_memory_block()
    for _mem in _new_memories:
        yield _sse({"type": "memory_saved", "content": _mem})
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
        prompt_identity = f"{system}\n\n{memory_block}{history_block}Question: {question}\nCiel:"
        yield from _stream_llm(prompt_identity, ollama_model, api_key, model)
        yield _sse({"type": "done", "sources": [], "confidence": confidence_val})
        return

    # RAG explanation — LLM for natural response.
    if _is_rag_query(question):
        system = _RAG_SYSTEM_VI if lang == "vi" else _RAG_SYSTEM_EN
        prompt_rag = f"{system}\n\n{memory_block}{history_block}Question: {question}\nCiel:"
        yield from _stream_llm(prompt_rag, ollama_model, api_key, model)
        yield _sse({"type": "done", "sources": [], "confidence": confidence_val})
        return

    try:
        yield _sse({"type": "step", "step": "embedding"})
        search_query = _rewrite_query_with_history(question, history, ollama_model, api_key)
        embed_query = _augment_for_embedding(search_query, history)
        vector = embed_text(embed_query)

        yield _sse({"type": "step", "step": "searching"})
        try:
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

            # Filename hits first, then by similarity. Cap at _TOP_K * 2.
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

        if not chunks and not hybrid and not has_prior_context:
            msg = (
                "Không tìm thấy thông tin liên quan trong tài liệu."
                if lang == "vi"
                else "No relevant information found in the documents."
            )
            yield _sse({"type": "done", "answer": msg, "sources": [], "confidence": confidence_val})
            return

        sources = []
        _seen_doc_ids: set[str] = set()
        for c in chunks:
            doc_id = c.get("document_id", "")
            if doc_id and doc_id in _seen_doc_ids:
                continue
            if doc_id:
                _seen_doc_ids.add(doc_id)
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

        yield _sse({"type": "sources", "sources": sources})

        if chunks:
            has_tabular = any("  |  " in (c.get("content") or "") for c in chunks[:5])
            if filename_doc_ids or has_tabular:
                filtered = chunks
            elif _RERANKER_ENABLED and _bge_rerank is not None:
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
                filtered = _llm_filter_chunks(question, chunks, ollama_model, api_key, groq_filter_model)
                if not filtered:
                    filtered = chunks

            # Rebuild sources — deduplicated by document_id
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

            parts = []
            for i, c in enumerate(filtered):
                section = c.get("section_title") or ""
                header = f"[{i+1}]" + (f" [{section}]" if section else "")
                parts.append(f"{header}\n{c['content'][:_MAX_CHUNK_CHARS]}")
            context = "\n\n".join(parts)

            if filename_doc_ids or has_tabular:
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
            prompt = f"{system}\n\n{memory_block}{history_block}Context:\n{context}\n\nQuestion: {question}\nAnswer:"
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
            prompt = f"{continuation_system}\n\n{memory_block}{history_block}Question: {question}\nAnswer:"
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
            prompt = f"{hybrid_system}\n\n{memory_block}{history_block}Question: {question}\nAnswer:"

        yield _sse({"type": "step", "step": "generating"})
        yield from _stream_llm(prompt, ollama_model, api_key, model)
        yield _sse({"type": "done", "sources": sources, "confidence": confidence_val})

    except Exception as exc:
        yield _sse({"type": "token", "token": f"Lỗi xử lý: {exc}"})
        yield _sse({"type": "done", "sources": [], "confidence": confidence_val})
