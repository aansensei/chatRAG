# shared/utils/extractors

Text extractors for every supported file type. Workers call these directly
(no dispatcher — the worker switches on `Path(file_path).suffix`).

---

## Files

| File | Handles | Notes |
|---|---|---|
| `base.py` | `ExtractResult` dataclass | Common output: `text`, `metadata`, `tables`, `images` |
| `dispatcher.py` | dispatcher (legacy) | Not used by `ocr_worker.py` — it dispatches inline |
| `pdf_extractor.py` | `.pdf` text layer | Falls back to OCR via `ocr_extractor` if needed |
| `ocr_extractor.py` | `.png` `.jpg` `.jpeg` `.tiff` `.bmp`, and image-only PDFs | PaddleOCR. Supports per-page progress callback. |
| `docx_extractor.py` | `.docx` | python-docx — paragraphs + tables joined with `  \|  ` |
| `office_extractor.py` | `.docx` `.xlsx` `.csv` | Newer entry. `extract_docx`, `extract_xlsx`, `extract_csv` |
| `xlsx_extractor.py` | `.xlsx` (legacy) | Now lives in `office_extractor.py` |
| `pptx_extractor.py` | `.pptx` | python-pptx — text frames + tables + image refs |

---

## `ExtractResult`

```python
class ExtractResult:
    text: str               # concatenated for embedding
    metadata: dict          # at minimum {"source": <filename>, "pages": N}
    tables: list[dict]      # optional, structured table data
    images: list[str]       # optional, extracted image paths
```

---

## CSV multi-encoding

`extract_csv` tries these encodings in order until one succeeds:

```
utf-8-sig -> utf-8 -> cp1258 -> cp1252 -> latin-1
```

This handles Windows Excel exports (often cp1258 for Vietnamese) cleanly.
Cells are joined with `  |  ` so the chunker keeps rows intact and the
retrieval pipeline's tabular detector treats them as structured data
(skips the LLM relevance filter to preserve numbers).
