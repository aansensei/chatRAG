## shared/utils/extractors

File content extractors. All calls go through `dispatcher.py` — the caller doesn't need to know the file type, just passes a path and gets back an `ExtractResult`.

### Files

`base.py` - `ExtractResult` dataclass: unified output format with `text`, `tables` (list of dicts), `images` (list of file paths), `metadata`.

`dispatcher.py` - single entry point. Routes by file extension to the correct extractor. Raises `ValueError` for unsupported types.

`pdf_extractor.py` - pymupdf for text and images, pdfplumber for tables (more accurate than pymupdf for complex table layouts).

`docx_extractor.py` - python-docx for text and tables, zipfile to extract embedded images (a docx file is essentially a zip archive).

`xlsx_extractor.py` - openpyxl reads each sheet; each sheet becomes a table dict and a flat text string for embedding. Empty sheets are skipped.

`pptx_extractor.py` - python-pptx reads each slide, extracting text frames, tables, and images. Text is prefixed with `[Slide N]` to retain positional context after chunking.
