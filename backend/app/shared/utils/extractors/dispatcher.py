from pathlib import Path
from .base import ExtractResult
from .pdf_extractor import extract_pdf
from .docx_extractor import extract_docx
from .xlsx_extractor import extract_xlsx
from .pptx_extractor import extract_pptx

SUPPORTED = {".pdf", ".docx", ".xlsx", ".xls", ".pptx", ".ppt"}


def extract(file_path: str, image_output_dir: str = "extracted_images") -> ExtractResult:
    ext = Path(file_path).suffix.lower()

    if ext not in SUPPORTED:
        raise ValueError(f"Unsupported file type: {ext}. Supported: {SUPPORTED}")

    if ext == ".pdf":
        return extract_pdf(file_path, image_output_dir)
    elif ext == ".docx":
        return extract_docx(file_path, image_output_dir)
    elif ext in {".xlsx", ".xls"}:
        return extract_xlsx(file_path)
    elif ext in {".pptx", ".ppt"}:
        return extract_pptx(file_path, image_output_dir)
