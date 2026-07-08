import re
from uuid import UUID

from app.domain.entities.chunk import Chunk
from .base import ChunkConfig

_MARKDOWN_HEADING_RE = re.compile(r"^#{1,3}\s+\S")
# Capitalized prefix only — avoids false positives like "phần giả định..."
_SECTION_PREFIX_RE = re.compile(
    r"^(?:Chapter|Unit|Section|Part|Chương|Phần|Mục)\s+[\w&]"
)


def _is_heading(line: str) -> bool:
    """
    Detect a heading line.
    Covers: Markdown (#/##/###), English/Vietnamese section prefixes,
    and ALL-CAPS lines in any language (including Vietnamese accented uppercase).
    Requires at least one space to avoid mistaking short IDs (CK-FIXED-01) for headings.
    """
    s = line.strip()
    if not s:
        return False
    if _MARKDOWN_HEADING_RE.match(s):
        return True
    if _SECTION_PREFIX_RE.match(s):
        return True
    # ALL-CAPS check: works for both ASCII and Unicode (Vietnamese, etc.)
    # Require: 6-80 chars, mostly alphabetic, all uppercase. Multi-word lines
    # (has a space) qualify outright; single-word lines only qualify if they're
    # a real word (letters only) — excludes short IDs like "CK-FIXED-01".
    letters = [c for c in s if c.isalpha()]
    has_space = " " in s
    single_real_word = not has_space and s.isalpha()
    return (
        6 <= len(s) <= 80
        and len(letters) >= 4
        and s.isupper()
        and (has_space or single_real_word)
    )


def _estimate_tokens(text: str) -> int:
    # rough approximation: 1 token ≈ 4 characters, good enough pre-embedding
    return max(1, len(text) // 4)


_LEADING_PAGE_MARKER_RE = re.compile(r"^\[Page (\d+)\]\n?")
_ANY_PAGE_MARKER_RE = re.compile(r"\[Page \d+\]\n?")


def _extract_page_number(content: str) -> tuple[int | None, str]:
    """A chunk that starts right where a PDF page begins carries an
    OCR-inserted "[Page N]" marker (see ocr_extractor.py) as its first line.
    Pull that leading page number out for citation purposes ("open the
    source PDF at page N") — it's the chunk's own starting page. Chunks that
    start mid-page (a long page split across several chunks) have no leading
    marker and get page_number=None; there's no reliable way to attribute
    those without tracking page boundaries as real chunk boundaries, which
    would fragment unrelated content unnecessarily.

    Strips every "[Page N]" marker in the chunk, not just the leading one —
    several short pages can end up merged into a single chunk, and any
    marker after the first would otherwise leak into the LLM prompt and the
    text shown to the user as literal, meaningless text."""
    m = _LEADING_PAGE_MARKER_RE.match(content)
    page_number = int(m.group(1)) if m else None
    cleaned = _ANY_PAGE_MARKER_RE.sub("", content)
    return page_number, cleaned


def _split_into_sections(text: str) -> list[tuple[str | None, str]]:
    """
    Split text on heading boundaries.
    Returns list of (section_title, section_body) pairs.
    Paragraphs before the first heading get title=None.
    """
    lines = text.splitlines(keepends=True)
    # store (char_pos, title, raw_line_len) so body_start uses the actual line length
    heading_positions: list[tuple[int, str, int]] = []
    pos = 0
    for line in lines:
        stripped = line.rstrip("\n\r")
        if _is_heading(stripped):
            heading_positions.append((pos, stripped.lstrip("#").strip(), len(line)))
        pos += len(line)

    if not heading_positions:
        return [(None, text.strip())]

    sections = []

    preamble = text[: heading_positions[0][0]].strip()
    if preamble:
        sections.append((None, preamble))

    for i, (start, title, line_len) in enumerate(heading_positions):
        body_start = start + line_len
        body_end = heading_positions[i + 1][0] if i + 1 < len(heading_positions) else len(text)
        body = text[body_start:body_end].strip()
        if body:
            sections.append((title, body))

    return sections


def _split_by_paragraph(text: str, max_tokens: int) -> list[str]:
    """
    Greedily accumulate paragraphs until adding the next one would exceed max_tokens.
    Falls back to word-level splitting only when a single paragraph is already over the limit.
    This ensures chunks never break mid-paragraph.
    """
    paragraphs = [p.strip() for p in re.split(r"\n\n+", text) if p.strip()]
    chunks = []
    current_parts: list[str] = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = _estimate_tokens(para)

        if para_tokens > max_tokens:
            # flush whatever we have accumulated first
            if current_parts:
                chunks.append("\n\n".join(current_parts))
                current_parts = []
                current_tokens = 0
            # paragraph alone exceeds limit — split at word level as last resort
            words = para.split()
            words_per_chunk = max(1, max_tokens * 4 // 5)
            for i in range(0, len(words), words_per_chunk):
                chunks.append(" ".join(words[i: i + words_per_chunk]))
        elif current_tokens + para_tokens > max_tokens:
            chunks.append("\n\n".join(current_parts))
            current_parts = [para]
            current_tokens = para_tokens
        else:
            current_parts.append(para)
            current_tokens += para_tokens

    if current_parts:
        chunks.append("\n\n".join(current_parts))

    return chunks


def chunk_text(
    text: str,
    document_id: UUID,
    config: ChunkConfig | None = None,
) -> list[Chunk]:
    if config is None:
        config = ChunkConfig()

    if not text or not text.strip():
        return []

    sections = _split_into_sections(text)
    raw_chunks: list[tuple[str | None, str]] = []

    for section_title, body in sections:
        if _estimate_tokens(body) <= config.max_tokens:
            raw_chunks.append((section_title, body))
        else:
            for part in _split_by_paragraph(body, config.max_tokens):
                raw_chunks.append((section_title, part))

    chunks = []
    for index, (title, content) in enumerate(raw_chunks):
        page_number, content = _extract_page_number(content)
        chunks.append(Chunk(
            document_id=document_id,
            content=content,
            chunk_index=index,
            token_count=_estimate_tokens(content),
            char_count=len(content),
            section_title=title,
            page_number=page_number,
        ))
    return chunks
