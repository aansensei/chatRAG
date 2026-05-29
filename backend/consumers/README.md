## consumers

Event consumer entry points. Mỗi file subscribe vào một domain event và kích hoạt bước tiếp theo trong pipeline. Mỗi consumer chạy như một process độc lập (hoặc coroutine riêng).

Pipeline event chain:
`DocumentUploaded` → `OcrCompleted` → `ChunkCreated` → `EmbeddingCompleted` → `LabelAssigned` → `ReviewApproved`

### Files

`document_uploaded_handler.py` - nhận `DocumentUploaded`, gọi extractor để lấy raw text. Nếu document có trang scan, trigger OCR. Nếu không, publish `ChunkCreated` luôn.

`ocr_completed_handler.py` - nhận `OcrCompleted`, gộp text OCR vào document, publish `ChunkCreated`.

`chunk_created_handler.py` - nhận `ChunkCreated`, gọi embedding model để vector hóa từng chunk, publish `EmbeddingCompleted`.

`embedding_handler.py` - nhận `EmbeddingCompleted`, upsert vectors vào Qdrant, gọi classifier để assign sensitivity label, publish `LabelAssigned`.

`review_handler.py` - nhận `LabelAssigned`, nếu sensitivity >= CONFIDENTIAL thì tạo Review và chờ. Nếu < CONFIDENTIAL thì chuyển Document sang READY ngay.
