import fitz  # pymupdf
import pdfplumber
from pathlib import Path
from .base import ExtractResult


def extract_pdf(file_path: str, image_output_dir: str = "extracted_images") -> ExtractResult:
    path = Path(file_path)
    image_dir = Path(image_output_dir)
    image_dir.mkdir(parents=True, exist_ok=True)

    result = ExtractResult()
    text_parts = []
    tables = []
    image_paths = []

    # text + images dùng pymupdf
    doc = fitz.open(file_path)
    for page_index, page in enumerate(doc):
        text_parts.append(page.get_text())

        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            ext = base_image["ext"]
            image_data = base_image["image"]

            save_path = image_dir / f"{path.stem}_p{page_index + 1}_img{img_index + 1}.{ext}"
            save_path.write_bytes(image_data)
            image_paths.append(str(save_path))

    doc.close()

    # tables dùng pdfplumber (chính xác hơn pymupdf cho bảng)
    with pdfplumber.open(file_path) as pdf:
        for page_index, page in enumerate(pdf.pages):
            for table_index, table in enumerate(page.extract_tables()):
                if not table:
                    continue
                header = table[0]
                rows = table[1:]
                tables.append({
                    "page": page_index + 1,
                    "table_index": table_index + 1,
                    "data": [
                        {header[i]: cell for i, cell in enumerate(row)}
                        for row in rows
                    ]
                })

    result.text = "\n".join(text_parts).strip()
    result.tables = tables
    result.images = image_paths
    result.metadata = {"pages": len(fitz.open(file_path)), "source": str(path)}

    return result
