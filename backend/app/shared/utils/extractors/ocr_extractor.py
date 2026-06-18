import fitz
from pathlib import Path
from .base import ExtractResult

_READER_CACHE: dict[tuple, object] = {}


def _get_reader(languages: tuple):
    if languages not in _READER_CACHE:
        import easyocr
        # gpu=False for CPU-only environments; set True if GPU available
        _READER_CACHE[languages] = easyocr.Reader(list(languages))
    return _READER_CACHE[languages]


def extract_ocr_pdf(
    file_path: str,
    languages: list[str] | None = None,
) -> ExtractResult:
    if languages is None:
        languages = ["en", "vi"]

    path = Path(file_path)
    reader = _get_reader(tuple(sorted(languages)))
    doc = fitz.open(file_path)
    page_count = len(doc)
    text_parts = []

    for page_index, page in enumerate(doc):
        # render at 2x resolution — significantly improves OCR accuracy on small text
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_bytes = pix.tobytes("png")
        lines = reader.readtext(img_bytes, detail=0, paragraph=True)
        page_text = "\n".join(lines).strip()
        if page_text:
            text_parts.append(f"[Page {page_index + 1}]\n{page_text}")

    doc.close()

    result = ExtractResult()
    result.text = "\n\n".join(text_parts).strip()
    result.metadata = {"pages": page_count, "source": str(path), "ocr": True}
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
