import zipfile
from pathlib import Path
from docx import Document
from .base import ExtractResult


def extract_docx(file_path: str, image_output_dir: str = "extracted_images") -> ExtractResult:
    path = Path(file_path)
    image_dir = Path(image_output_dir)
    image_dir.mkdir(parents=True, exist_ok=True)

    result = ExtractResult()
    doc = Document(file_path)
    text_parts = []
    tables = []
    image_paths = []

    # text: đọc từng paragraph
    for para in doc.paragraphs:
        if para.text.strip():
            text_parts.append(para.text.strip())

    # tables: mỗi bảng thành list of dict, row đầu tiên làm header
    for table_index, table in enumerate(doc.tables):
        rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
        if not rows:
            continue
        header = rows[0]
        data = [
            {header[i]: cell for i, cell in enumerate(row)}
            for row in rows[1:]
        ]
        tables.append({
            "table_index": table_index + 1,
            "data": data
        })

    # images: docx thực ra là file zip, ảnh nằm trong word/media/
    with zipfile.ZipFile(file_path, "r") as z:
        for name in z.namelist():
            if name.startswith("word/media/"):
                filename = Path(name).name
                save_path = image_dir / f"{path.stem}_{filename}"
                save_path.write_bytes(z.read(name))
                image_paths.append(str(save_path))

    result.text = "\n".join(text_parts)
    result.tables = tables
    result.images = image_paths
    result.metadata = {"source": str(path)}

    return result
