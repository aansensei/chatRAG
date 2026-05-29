## workers

Long-running background processes. Mỗi worker xử lý một giai đoạn cụ thể trong ingestion pipeline. Chạy song song độc lập với API server.

Mỗi worker nhận message từ queue (Kafka hoặc Redis), xử lý, rồi publish message tiếp theo. Một worker crash không ảnh hưởng các worker khác.

### Files

`ingestion_worker.py` - orchestrator worker, điều phối toàn bộ pipeline cho một document: nhận upload request, gọi các workers theo thứ tự, update IngestJob status.

`ocr_worker.py` - nhận trang scan image, chạy PaddleOCR, trả về text. Chạy trên GPU nếu có.

`chunk_worker.py` - nhận raw text, cắt thành chunks theo strategy (sentence, paragraph, hoặc token-based). Tạo Chunk entities và lưu DB.

`embedding_worker.py` - nhận list of chunks, chạy embedding model, trả về vectors. Batch processing để tối ưu throughput.

`vector_worker.py` - nhận embeddings, upsert vào Qdrant collection. Đảm bảo idempotent - upsert an toàn nếu chunk đã tồn tại.

`classify_worker.py` - nhận extracted text, chạy sensitivity classifier, update Document.sensitivity, trigger review nếu cần.

`review_worker.py` - nhận review decision (approve/reject), cập nhật Document status tương ứng.
