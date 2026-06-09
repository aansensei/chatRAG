import re
import fitz  # pymupdf
import pdfplumber
from pathlib import Path
from .base import ExtractResult

# Unicode Private Use Area (U+E000–U+F8FF): unmapped math font glyphs, not readable text
_PUA_RE = re.compile(r"[-]")


def _is_meaningful_header(header: list) -> bool:
    # a header cell is meaningful if it has more than 1 char and is not purely numeric
    def meaningful(cell) -> bool:
        if not cell or not cell.strip():
            return False
        h = cell.strip()
        if len(h) <= 1:
            return False
        if h.replace(".", "").replace("-", "").replace(" ", "").isdigit():
            return False
        return True

    return any(meaningful(cell) for cell in header)


def extract_pdf(file_path: str, image_output_dir: str = "extracted_images") -> ExtractResult:
    path = Path(file_path)
    image_dir = Path(image_output_dir)
    image_dir.mkdir(parents=True, exist_ok=True)

    result = ExtractResult()
    text_parts = []
    tables = []
    image_paths = []

    # text and images via pymupdf
    doc = fitz.open(file_path)
    page_count = len(doc)
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

    # tables via pdfplumber — more accurate than pymupdf for complex table layouts
    with pdfplumber.open(file_path) as pdf:
        for page_index, page in enumerate(pdf.pages):
            for table_index, table in enumerate(page.extract_tables()):
                if not table:
                    continue
                header = table[0]
                if not _is_meaningful_header(header):
                    continue
                rows = table[1:]
                tables.append({
                    "page": page_index + 1,
                    "table_index": table_index + 1,
                    "data": [
                        {header[i]: cell for i, cell in enumerate(row)}
                        for row in rows
                    ]
                })

    raw_text = "\n".join(text_parts).strip()
    result.text = _PUA_RE.sub("", raw_text)
    result.tables = tables
    result.images = image_paths
    result.metadata = {"pages": page_count, "source": str(path)}

    return result

