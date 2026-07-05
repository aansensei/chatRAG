"""Lightweight LLM-based entity/relationship extraction for the GraphRAG POC.

Scoped intentionally small: one prompt, one JSON parse, no schema validation
library. Good enough to test whether graph-augmented retrieval helps with
multi-hop questions before investing in a heavier pipeline.
"""
import json
import logging
import re

from app.application.retrieval.ask_question import _call_llm_once

logger = logging.getLogger(__name__)

_MAX_CHUNK_CHARS = 3000

_PROMPT = """Trích xuất các thực thể (entity) và mối quan hệ (relation) có trong đoạn văn bản dưới đây.

Chỉ trích xuất thực thể có tên riêng cụ thể (tổ chức, dự án, hợp đồng, con người, sản phẩm/công nghệ, số tiền/ngân sách cụ thể...). Bỏ qua khái niệm chung chung.

QUAN TRỌNG — một quan hệ (relation) chỉ nối được đúng 2 thực thể. Nếu một sự kiện trong văn bản thực ra liên quan đến 3 thực thể trở lên (vd: "A phân bổ X tỷ VND cho giai đoạn B"), đừng chỉ trích 1 quan hệ — hãy tách thành NHIỀU quan hệ nhị phân để không mất liên kết nào, ví dụ:
- A -> phân bổ -> X tỷ VND
- X tỷ VND -> dành cho -> B
- A -> phân bổ ngân sách cho -> B
Áp dụng cách tách này cho MỌI câu có từ 3 thực thể liên quan trở lên.

Trả lời DUY NHẤT bằng JSON theo đúng schema sau, không thêm giải thích, không dùng markdown code fence:
{{"entities": [{{"name": "...", "type": "..."}}], "relations": [{{"source": "...", "relation": "...", "target": "...", "description": "..."}}]}}

"type" là nhãn ngắn gọn (vd: organization, project, contract, person, technology, budget, date). "source"/"target" phải khớp chính xác với "name" trong danh sách entities. Nếu đoạn văn không có quan hệ rõ ràng nào, trả về relations rỗng.

===== VĂN BẢN =====
{text}
===== HẾT VĂN BẢN =====
"""


def _extract_json(raw: str) -> dict | None:
    raw = raw.strip()
    raw = re.sub(r"^```(json)?", "", raw).strip()
    raw = re.sub(r"```$", "", raw).strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    try:
        return json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return None


def extract_entities_relations(chunk_text: str, model: str, api_key: str) -> tuple[list[dict], list[dict]]:
    """Returns (entities, relations) parsed from one chunk. Empty lists on any failure."""
    text = chunk_text[:_MAX_CHUNK_CHARS]
    prompt = _PROMPT.format(text=text)
    raw = _call_llm_once(prompt, model, api_key, max_tokens=800)
    if not raw:
        return [], []
    parsed = _extract_json(raw)
    if not parsed:
        logger.warning("extract_entities_relations: could not parse JSON from LLM output")
        return [], []

    entities = [
        {"name": str(e.get("name", "")).strip(), "type": str(e.get("type", "")).strip() or "unknown"}
        for e in parsed.get("entities", [])
        if isinstance(e, dict) and str(e.get("name", "")).strip()
    ]
    known_names = {e["name"] for e in entities}
    relations = [
        {
            "source": str(r.get("source", "")).strip(),
            "relation": str(r.get("relation", "")).strip(),
            "target": str(r.get("target", "")).strip(),
            "description": str(r.get("description", "")).strip(),
        }
        for r in parsed.get("relations", [])
        if isinstance(r, dict)
        and str(r.get("source", "")).strip() in known_names
        and str(r.get("target", "")).strip() in known_names
        and str(r.get("relation", "")).strip()
    ]
    return entities, relations
