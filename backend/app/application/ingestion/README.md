## application/ingestion

Use cases điều phối ingestion pipeline.

### Files

`start_ingestion.py` - tạo IngestJob mới cho document, publish `DocumentUploaded` event để kick off pipeline. Đây là trigger điểm đầu tiên.

`retry_job.py` - retry một IngestJob đang ở trạng thái FAILED. Reset về trạng thái trước bước bị fail thay vì chạy lại từ đầu.
