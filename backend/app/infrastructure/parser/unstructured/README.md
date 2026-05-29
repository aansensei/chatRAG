## infrastructure/parser/unstructured

Unstructured.io integration cho layout-aware parsing.

### Files

`parser.py` - parse document thành danh sách elements có type (Title, NarrativeText, Table, Image, ...). Output này giúp chunker giữ nguyên cấu trúc logic thay vì cắt brute-force theo token count.
