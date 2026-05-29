## domain/events

Domain events - payload cho message queue. Mỗi event đánh dấu một việc đã xảy ra trong pipeline và trigger bước tiếp theo. Consumers ở `consumers/` subscribe vào từng event này.

Pipeline flow theo thứ tự: document_uploaded → ocr_completed → chunk_created → embedding_completed → label_assigned → review_approved (nếu cần)

### Files

`document_uploaded.py` - document đã được lưu vào storage, sẵn sàng để extract text.

`ocr_completed.py` - OCR đã xong trên các trang scan. Trigger chunking.

`chunk_created.py` - text đã được cắt thành chunks. Trigger embedding.

`embedding_completed.py` - toàn bộ chunks đã được vector hóa. Trigger indexing vào Qdrant.

`label_assigned.py` - sensitivity label đã được assign. Nếu CONFIDENTIAL+, trigger tạo Review.

`review_approved.py` - reviewer đã duyệt document. Document chuyển sang READY.
