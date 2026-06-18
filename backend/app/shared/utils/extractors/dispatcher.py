from pathlib import Path
from .base import ExtractResult
from .pdf_extractor import extract_pdf
from .docx_extractor import extract_docx
from .xlsx_extractor import extract_xlsx
from .pptx_extractor import extract_pptx
from .ocr_extractor import extract_ocr_pdf, extract_ocr_image

SUPPORTED = {".pdf", ".docx", ".xlsx", ".xls", ".pptx", ".ppt", ".png", ".jpg", ".jpeg"}

# PDF pages with fewer characters than this are considered image-only (scanned)
_OCR_TEXT_THRESHOLD = 50


def extract(
    file_path: str,
    image_output_dir: str = "extracted_images",
    languages: list[str] | None = None,
) -> ExtractResult:
    ext = Path(file_path).suffix.lower()

    if ext not in SUPPORTED:
        raise ValueError(f"Unsupported file type: {ext}. Supported: {SUPPORTED}")

    if ext == ".pdf":
        result = extract_pdf(file_path, image_output_dir)
        # scanned PDF: no meaningful text extracted → fall back to OCR
        if len(result.text.strip()) < _OCR_TEXT_THRESHOLD:
            return extract_ocr_pdf(file_path, languages)
        return result

    if ext == ".docx":
        return extract_docx(file_path, image_output_dir)

    if ext in {".xlsx", ".xls"}:
        return extract_xlsx(file_path)

    if ext in {".pptx", ".ppt"}:
        return extract_pptx(file_path, image_output_dir)

    if ext in {".png", ".jpg", ".jpeg"}:
        return extract_ocr_image(file_path, languages)
