from pathlib import Path
from openpyxl import load_workbook
from .base import ExtractResult


def extract_xlsx(file_path: str) -> ExtractResult:
    path = Path(file_path)
    result = ExtractResult()
    wb = load_workbook(file_path, data_only=True)
    tables = []
    text_parts = []

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = list(ws.iter_rows(values_only=True))

        # bỏ qua sheet trống
        non_empty = [r for r in rows if any(c is not None for c in r)]
        if not non_empty:
            continue

        header = [str(c) if c is not None else f"col_{i}" for i, c in enumerate(non_empty[0])]
        data = [
            {header[i]: cell for i, cell in enumerate(row)}
            for row in non_empty[1:]
        ]
        tables.append({
            "sheet": sheet_name,
            "data": data
        })

        # text: mỗi sheet ghép thành chuỗi để dễ embed sau này
        for row in non_empty:
            line = " | ".join(str(c) for c in row if c is not None)
            if line.strip():
                text_parts.append(line)

    result.text = "\n".join(text_parts)
    result.tables = tables
    result.metadata = {"sheets": wb.sheetnames, "source": str(path)}

    return result
