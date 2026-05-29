## scheduler

Background scheduled tasks chạy định kỳ, không phải trigger theo event. Dùng APScheduler hoặc celery-beat tùy config.

### Files

`bootstrap_ingestion.py` - chạy một lần khi system khởi động lần đầu, ingest toàn bộ documents có sẵn.

`cleanup.py` - cleanup định kỳ: xóa IngestJob cũ đã COMPLETED/FAILED quá N ngày, xóa orphaned chunks không còn document parent.

`delta_ingestion.py` - chạy theo schedule, detect documents đã thay đổi kể từ lần cuối ingest (check by hash hoặc modified_at), re-trigger ingestion cho chúng.

`retry_failed_jobs.py` - tự động retry các IngestJob bị FAILED sau một khoảng thời gian, giới hạn số lần retry để tránh infinite loop.
