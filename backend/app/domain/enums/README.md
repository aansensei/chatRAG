## domain/enums

Shared enums dùng chung giữa entities và services. Tất cả extend `(str, Enum)` để serialize thành string thay vì int trong JSON và Pydantic - quan trọng khi lưu vào DB và trả về API.

### Files

`job_status.py` - trạng thái của pipeline và review workflow.

- `IngestJobStatus`: PENDING → EXTRACTING → CHUNKING → EMBEDDING → INDEXING → COMPLETED (hoặc FAILED bất kỳ bước nào)
- `ReviewStatus`: PENDING / APPROVED / REJECTED cho human review

`sensitivity.py` - phân loại và trạng thái liên quan đến document.

- `SensitivityLevel`: PUBLIC < INTERNAL < CONFIDENTIAL < SECRET - quyết định luồng xử lý (review bắt buộc với CONFIDENTIAL+)
- `DocumentStatus`: PROCESSING → READY (hoặc FAILED / ARCHIVED)
- `UserRole`: ADMIN / USER / VIEWER - dùng để guard routes ở presentation layer
