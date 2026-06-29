import fitz
import re
from pathlib import Path
from .base import ExtractResult

_READER_CACHE: dict[tuple, object] = {}

_MIN_TEXT_CHARS_PER_PAGE = 30


def _get_reader(languages: tuple):
    if languages not in _READER_CACHE:
        import easyocr
        _READER_CACHE[languages] = easyocr.Reader(list(languages))
    return _READER_CACHE[languages]


def _page_has_text(page) -> bool:
    return len(page.get_text("text").strip()) >= _MIN_TEXT_CHARS_PER_PAGE


def extract_ocr_pdf(
    file_path: str,
    languages: list[str] | None = None,
    on_page_done: "callable[[int, int], None] | None" = None,
) -> ExtractResult:
    if languages is None:
        languages = ["en", "vi"]

    path = Path(file_path)
    doc = fitz.open(file_path)
    page_count = len(doc)
    text_parts = []

    sample_pages = [doc[i] for i in range(min(3, page_count))]
    is_digital = any(_page_has_text(p) for p in sample_pages)

    if is_digital:
        for page_index, page in enumerate(doc):
            blocks = page.get_text("blocks")
            block_texts = []
            for b in blocks:
                if b[6] == 0:
                    b_text = b[4].strip()
                    b_text = re.sub(r'(?<!\n)\n(?!\n)', ' ', b_text)
                    if b_text:
                        block_texts.append(b_text)
            page_text = "\n\n".join(block_texts)
            
            if page_text:
                text_parts.append(f"[Page {page_index + 1}]\n{page_text}")
            if on_page_done:
                on_page_done(page_index + 1, page_count)
    else:
        reader = _get_reader(tuple(sorted(languages)))
        for page_index, page in enumerate(doc):
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_bytes = pix.tobytes("png")
            lines = reader.readtext(img_bytes, detail=0, paragraph=True)
            page_text = "\n".join(lines).strip()
            if page_text:
                text_parts.append(f"[Page {page_index + 1}]\n{page_text}")
            if on_page_done:
                on_page_done(page_index + 1, page_count)

    doc.close()

    result = ExtractResult()
    result.text = "\n\n".join(text_parts).strip()
    result.metadata = {
        "pages": page_count,
        "source": str(path),
        "ocr": not is_digital,
    }
    return result


def extract_ocr_image(
    file_path: str,
    languages: list[str] | None = None,
) -> ExtractResult:
    if languages is None:
        languages = ["en", "vi"]

    path = Path(file_path)
    reader = _get_reader(tuple(sorted(languages)))
    lines = reader.readtext(str(path), detail=0, paragraph=True)

    result = ExtractResult()
    result.text = "\n".join(lines).strip()
    result.metadata = {"source": str(path), "ocr": True}
    return result
