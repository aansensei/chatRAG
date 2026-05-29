## infrastructure/classifier

Sensitivity classification cho documents.

### Files

`sensitivity_model.py` - nhận text đã extract, trả về SensitivityLevel. Có thể là rule-based (keyword matching) hoặc ML model. Kết quả được IngestJob dùng để quyết định có cần trigger review không.
