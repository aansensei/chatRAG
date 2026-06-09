import re
from uuid import UUID

from app.domain.entities.chunk import Chunk
from .base import ChunkConfig

# Three heading forms (all printable ASCII only — excludes unicode math symbols):
# 1. Markdown: # / ## / ###
# 2. Document section prefix: Chapter / Unit / Section / Part followed by number
# 3. ALL-CAPS line: letters, digits, spaces and :&()- only, min 6 chars
_HEADING_RE = re.compile(
    r"^("
    r"#{1,3}\s+[ -~]+"
    r"|(?:Chapter|Unit|Section|Part)\s+[\w&]+[ -~]{0,80}"
    r"|[A-Z][A-Z0-9 :&()-]{5,59}"
    r")$",
    re.MULTILINE,
)


def _estimate_tokens(text: str) -> int:
    # rough approximation: 1 token ≈ 4 characters, good enough pre-embedding
    return max(1, len(text) // 4)


def _split_into_sections(text: str) -> list[tuple[str | None, str]]:
    """
    Split text on heading boundaries.
    Returns list of (section_title, section_body) pairs.
    Paragraphs before the first heading get title=None.
    """
    matches = list(_HEADING_RE.finditer(text))

    if not matches:
        return [(None, text.strip())]

    sections = []

    # text before first heading
    preamble = text[: matches[0].start()].strip()
    if preamble:
        sections.append((None, preamble))

    for i, match in enumerate(matches):
        title = match.group(0).lstrip("#").strip()
        body_start = match.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[body_start:body_end].strip()
        if body:
            sections.append((title, body))

    return sections


def _sliding_window(
    text: str, max_tokens: int, overlap_tokens: int
) -> list[str]:
    """
    Split a single long text into overlapping token windows.
    Works at the word level — avoids splitting mid-word.
    """
    words = text.split()
    # convert token limits to word counts (same 4-char heuristic)
    words_per_chunk = max(1, max_tokens * 4 // 5)
    overlap_words = max(0, overlap_tokens * 4 // 5)

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + words_per_chunk, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = end - overlap_words

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
            for window in _sliding_window(body, config.max_tokens, config.overlap_tokens):
                raw_chunks.append((section_title, window))

    return [
        Chunk(
            document_id=document_id,
            content=content,
            chunk_index=index,
            token_count=_estimate_tokens(content),
            char_count=len(content),
            section_title=title,
        )
        for index, (title, content) in enumerate(raw_chunks)
    ]
