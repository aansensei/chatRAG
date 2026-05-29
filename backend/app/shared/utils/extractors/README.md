## shared/utils/extractors

File content extractors. Tất cả đi qua `dispatcher.py` - caller không cần biết file type, chỉ cần pass path và nhận `ExtractResult`.

### Files

`base.py` - `ExtractResult` dataclass: unified output format với `text`, `tables` (list of dict), `images` (list of paths), `metadata`.

`dispatcher.py` - single entry point. Route theo file extension đến đúng extractor. Raise `ValueError` với unsupported type.

`pdf_extractor.py` - dùng pymupdf cho text và images, pdfplumber cho tables (chính xác hơn pymupdf với bảng phức tạp).

`docx_extractor.py` - python-docx cho text và tables, zipfile để extract embedded images (docx về bản chất là file zip).

`xlsx_extractor.py` - openpyxl đọc từng sheet, mỗi sheet thành table dict và flat text để embed. Bỏ qua sheet trống.

`pptx_extractor.py` - python-pptx đọc từng slide, extract text frame, tables, và images. Text được prefix bằng `[Slide N]` để retain context sau khi chunk.
